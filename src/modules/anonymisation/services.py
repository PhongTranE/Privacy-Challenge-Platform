from flask import current_app
from src.extensions import db
from src.core.services.file_manager import FileManager
from src.core.services.anonym_manager import AnonymManager
from src.core.utils import generate_secure_filename
from src.modules.anonymisation.models import AnonymModel
import os
from concurrent.futures import ThreadPoolExecutor
from src.constants.core_msg import *
from http import HTTPStatus
from flask_jwt_extended import get_jwt

class AnonymService:
    """Handles anonymization processing and business logic."""

    executor = ThreadPoolExecutor(max_workers=4)

    @staticmethod
    def process_anonymization(file):
        """Processes an uploaded anonymized file asynchronously."""

        jwt_claims = get_jwt()
        group_id = jwt_claims.get("group")  # Ensure the group_id is included in the JWT claims

        if not group_id:
            return {"message": "User must be part of a group to submit anonymization."}, HTTPStatus.FORBIDDEN
        file_manager = FileManager(upload_dir="anonym_file", allowed_extensions={"zip"})
        filename = f"{generate_secure_filename()}.zip"
        file_path = file_manager.save_file(file, filename=filename)
        extracted_file_path = file_manager.unzip_file(file_path)

        # Generate related file paths
        f_file_manager = FileManager(upload_dir="footprint", allowed_extensions={"json"})
        footprint_file = f"{f_file_manager.upload_dir}/{generate_secure_filename()}.json"
        s_file_manager = FileManager(upload_dir="shuffled_file", allowed_extensions={"json"})
        shuffled_file = f"{s_file_manager.upload_dir}/{generate_secure_filename()}.csv"

        original_file = current_app.config.get("ORIGINAL_FILE_PATH")

        if not original_file:
            return {"message": ORIGIN_FILE_NOT_FOUND}, HTTPStatus.BAD_REQUEST

        anonym_model = AnonymModel(
            footprint_file=footprint_file,
            shuffled_file=shuffled_file[:-4],
            original_file=original_file[:-4],
            file_link=extracted_file_path[:-4],
            name=os.path.splitext(file.filename)[0],  # Remove ".zip"
            status="processing",
            group_id=group_id
        )
        db.session.add(anonym_model)
        db.session.commit()

        current_app.logger.info(f"Submitting anonymization task for {anonym_model.id}")
        app_obj = current_app._get_current_object()
        AnonymService.executor.submit(AnonymService.run_anonymization, app_obj, anonym_model.id, extracted_file_path, original_file, shuffled_file, footprint_file)

        return {"message": "Processing started.", "anonym_id": anonym_model.id}, HTTPStatus.CREATED

    @staticmethod
    def run_anonymization(app, anonym_id, input_file, origin_file, shuffled_file, footprint_file):
        """Background anonymization task."""
        with app.app_context():
            try:
                anonym = AnonymManager(app, input_file, origin_file, shuffled_file, footprint_file)
                utility_score, naive_attack_score = anonym.process()

                anonym_model = db.session.query(AnonymModel).get(anonym_id)
                if anonym_model:
                    anonym_model.status = "completed"
                    anonym_model.utility = utility_score
                    anonym_model.naive_attack = naive_attack_score
                    db.session.commit()
                    current_app.logger.info(f"Anonymization completed for ID {anonym_id}")
            
            except Exception as e:
                db.session.rollback()
                anonym_model = db.session.query(AnonymModel).get(anonym_id)
                if anonym_model:
                    anonym_model.status = f"failed with Error: {str(e)}"
                    db.session.commit()
                    current_app.logger.error(f"Anonymization failed for ID {anonym_id}: {str(e)}")
                    raise Exception(str(e))

def validate_submission_limit(group_id: int) -> str:
    """Check if the team has exceeded submission or publish limits."""
    # Kiểm tra số lượng file đã upload
    total_files = db.session.query(AnonymModel).filter_by(group_id=group_id).count()
    if total_files > 20:
        return "Your group have reached the maximum limit of 20 submissions."

    # Kiểm tra số lượng file đã publish
    total_published = db.session.query(AnonymModel).filter_by(group_id=group_id, is_published=True).count()
    if total_published > 3:
        return "Your group have reached the maximum limit of 3 published submissions."
    
    return ""