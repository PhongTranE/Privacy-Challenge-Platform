import json
from sqlalchemy import select
from flask import current_app, jsonify
from src.extensions import db
from src.modules.attack.models import AttackModel
from src.modules.anonymisation.models import AnonymModel
from http import HTTPStatus
from src.core.services.file_manager import FileManager
from src.core.utils import generate_secure_filename


class AttackService:
    @staticmethod
    def save_file_attack_json(file):
        file_manager = FileManager(upload_dir="footprint", allowed_extensions={"json"})
        try:
            footprint_file = file_manager.save_file(file, f"{generate_secure_filename()}.json")
        except Exception as e:
            raise Exception(str(e))
        return footprint_file
    
    @staticmethod
    def check_attack_json(original_json_path, user_json_path, anonym_id, group_id):
        """
        Compares a user's attack JSON file against the original JSON data.
        """

        try:
            print(original_json_path)
            print(user_json_path)
            with open(original_json_path, "r", encoding="utf-8") as file:
                original_data = json.load(file)
            with open(user_json_path, "r", encoding="utf-8") as file:
                user_data = json.load(file)

        except (FileNotFoundError, json.JSONDecodeError) as e:
            current_app.logger.error(f"Error loading JSON files: {str(e)}")
            return jsonify({"error": "Invalid JSON file or format."}), HTTPStatus.BAD_REQUEST

        score_max = 0
        score = 0

        # Validate structure
        for identifier, months in original_data.items():
            if identifier not in user_data:
                current_app.logger.warning(f"Missing identifier {identifier} in user submission.")
                return jsonify({"error": f"Missing identifier {identifier}"}), HTTPStatus.BAD_REQUEST

            for month, ids in months.items():
                score_max += 1  # Increase max score for each month

                if month not in user_data[identifier]:
                    continue  # If the month is missing, move on

                # Get the valid ID from the original data
                valid_id = original_data[identifier][month][0]  # Always a single element

                # If the user correctly guessed the ID
                if valid_id in user_data[identifier][month]:
                    score += 1 / len(user_data[identifier][month])  # Weight based on number of guesses

        # Avoid division by zero
        final_score = score / score_max if score_max > 0 else 0

        # Store the attack attempt in the database
        attack_record = AttackModel(
            score=final_score,
            file=user_json_path,
            anonym_id=anonym_id,
            group_id=group_id
        )
        db.session.add(attack_record)
        db.session.commit()

        current_app.logger.info(f"Attack processed: {attack_record}")

        return jsonify({"score": final_score}), HTTPStatus.OK
    
    @staticmethod
    def process_attack(file, anonym_id, group_id):
        try:
            # Save the uploaded file
            file_path = AttackService.save_file_attack_json(file)

            # Fetch the original JSON path for the given anonym_id
            stmt = select(AnonymModel.footprint_file).where(AnonymModel.id == anonym_id)
            result = db.session.execute(stmt).scalar()

            if not result:
                return jsonify({"error": "Anonymisation record not found."}), HTTPStatus.NOT_FOUND

            original_json_path = result  # The footprint file path

            # Validate input parameters
            if not (file_path and original_json_path and anonym_id and group_id):
                return jsonify({"error": "Missing required parameters."}), HTTPStatus.BAD_REQUEST

            # Process attack evaluation
            return AttackService.check_attack_json(original_json_path, file_path, anonym_id, group_id)

        except Exception as e:
            current_app.logger.error(f"Error processing attack: {str(e)}")
            return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
