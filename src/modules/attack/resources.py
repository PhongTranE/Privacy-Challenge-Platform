from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, jsonify, send_file
from http import HTTPStatus
from src.extensions import db
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from src.modules.attack.services import AttackService
from src.modules.auth.models import GroupUserModel, UserModel
from src.modules.anonymisation.models import AnonymModel
from src.modules.attack.models import AttackModel
from src.common.response_builder import ResponseBuilder
import os
from src.modules.admin.services import group_not_banned_required
from sqlalchemy import func

blp = Blueprint("attack_func", __name__, description="Attack Management")

@blp.route("/<int:anonym_id>/upload")
class AttackUpload(MethodView):
    """
    Upload an attack file for a specific anonym file.
    """
    @jwt_required()
    @group_not_banned_required()
    def post(self, anonym_id):
        """
        Upload an attack file for a specific anonym file.
        """
        if "file" not in request.files:
            abort(HTTPStatus.BAD_REQUEST, message="No file uploaded.")

        file = request.files["file"]

        jwt_claims = get_jwt()
        user_group = jwt_claims.get("group", None) 

        return AttackService.process_attack(file, anonym_id, user_group)

@blp.route("/teams-with-published")
class TeamsWithPublished(MethodView):
    """
    Get the list of teams with published files.
    """
    @jwt_required()
    def get(self):
        """
        Get the list of teams with published files.
        """
        user_id = get_jwt_identity()
        user = db.session.get(UserModel, user_id)
        my_group_id = user.group_id if user else None

        groups = (
            db.session.query(GroupUserModel)
            .join(AnonymModel, GroupUserModel.id == AnonymModel.group_id)
            .filter(AnonymModel.is_published == True)
            .filter(GroupUserModel.id != my_group_id)
            .distinct()
            .all()
        )

        result = []
        for group in groups:
            num_published = (
                db.session.query(AnonymModel)
                .filter_by(group_id=group.id, is_published=True)
                .count()
            )
            result.append({
                "id": group.id,
                "name": group.name,
                "num_published": num_published
            })
        return ResponseBuilder().success(
            message="Fetched teams with published files.",
            data=result,
            status_code=HTTPStatus.OK
        ).build()

@blp.route("/<int:group_id>/published-files")
class GroupPublishedFiles(MethodView):
    """
    Get the list of published files for a specific group.
    """
    @jwt_required()
    def get(self, group_id):
        """
        Get the list of published files for a specific group.
        """
        files = (
            db.session.query(AnonymModel)
            .filter_by(group_id=group_id, is_published=True)
            .all()
        )
        result = [
            {
                "id": f.id,
                "name": f.name,
                "utility": f.utility,
                "naive_attack": f.naive_attack,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in files
        ]
        return ResponseBuilder().success(
            message="Fetched published files for group.",
            data=result,
            status_code=HTTPStatus.OK
        ).build()

@blp.route("/<int:anonym_id>/my-score")
class MyAttackScore(MethodView):
    """
    Get the attack score of a group for a specific anonym file.
    """
    @jwt_required()
    def get(self, anonym_id):
        user_id = get_jwt_identity()
        user = db.session.get(UserModel, user_id)
        my_group_id = user.group_id if user else None

        score = (
            db.session.query(func.max(AttackModel.score))
            .filter_by(anonym_id=anonym_id, group_id=my_group_id)
            .scalar()
        ) or 0

        return ResponseBuilder().success(
            message="Fetched your attack score.",
            data={"score": score},
            status_code=HTTPStatus.OK
        ).build()

@blp.route("/<int:anonym_id>/my-attacks")
class MyAttackHistory(MethodView):
    """
    Get the attack history of a group for a specific anonym file.
    """
    @jwt_required()
    def get(self, anonym_id):
        """
        Get the attack history of a group for a specific anonym file.
        """
        user_id = get_jwt_identity()
        user = db.session.get(UserModel, user_id)
        my_group_id = user.group_id if user else None

        attacks = (
            db.session.query(AttackModel)
            .filter_by(anonym_id=anonym_id, group_id=my_group_id)
            .order_by(AttackModel.id.desc())
            .all()
        )
        result = [
            {
                "id": a.id,
                "score": a.score,
                "file": a.file
            }
            for a in attacks
        ]
        return ResponseBuilder().success(
            message="Fetched your attack history.",
            data=result,
            status_code=HTTPStatus.OK
        ).build()

@blp.route("/<int:anonym_id>/download")
class DownloadAnonymFile(MethodView):
    """
    Download the anonym file for a specific anonym file.
    """
    @jwt_required()
    @group_not_banned_required()
    def get(self, anonym_id):
        """
        Download the anonym file for a specific anonym file.
        """
        anonym = db.session.get(AnonymModel, anonym_id)
        if not anonym or not anonym.is_published:
            abort(HTTPStatus.NOT_FOUND, message="File not found or not published.")
        file_path = anonym.shuffled_file + ".csv"
        if not file_path or not os.path.exists(file_path):
            abort(HTTPStatus.NOT_FOUND, message="File not found on disk")
        filename = f"{anonym.name}_anonymous.csv"
        return send_file(file_path, as_attachment=True, download_name=filename)

@blp.route("/<int:anonym_id>/history")
class AttackHistoryAll(MethodView):
    """
    Get all attack history for a specific anonym file (all teams).
    """
    @jwt_required()
    def get(self, anonym_id):
        """
        Get all attack history for a specific anonym file (all teams).
        """
        attacks = (
            db.session.query(AttackModel, GroupUserModel)
            .join(GroupUserModel, AttackModel.group_id == GroupUserModel.id)
            .filter(AttackModel.anonym_id == anonym_id)
            .order_by(AttackModel.id.desc())
            .all()
        )
        result = [
            {
                "id": a.AttackModel.id,
                "score": a.AttackModel.score,
                "attackerId": a.GroupUserModel.id,
                "attackerName": a.GroupUserModel.name,
                "file": a.AttackModel.file
            }
            for a in attacks
        ]
        return ResponseBuilder().success(
            message="Fetched all attack history for this file.",
            data=result,
            status_code=HTTPStatus.OK
        ).build()

@blp.route("/list/<int:group_id_attack>")
class AttackListByGroup(MethodView):
    """
    Get all groups attacked by a specific group, with minimal attack info.
    """
    def get(self, group_id_attack):
        """
        Get all groups attacked by a specific group, with minimal attack info.
        """
        # Subquery: For each file (anonym_id) of each group, get the max score that group_id_attack achieved
        file_max_score_subq = (
            db.session.query(
                AnonymModel.group_id.label('defense_group_id'),
                AnonymModel.id.label('anonym_id'),
                AnonymModel.name.label('anonym_name'),
                func.max(AttackModel.score).label('max_score')
            )
            .join(AttackModel, AttackModel.anonym_id == AnonymModel.id)
            .filter(AttackModel.group_id == group_id_attack)
            .group_by(AnonymModel.group_id, AnonymModel.id, AnonymModel.name)
        ).subquery()

        # Subquery: For each group, get the minimal max_score (attack_score)
        min_file_score_subq = (
            db.session.query(
                file_max_score_subq.c.defense_group_id,
                func.min(file_max_score_subq.c.max_score).label('attack_score')
            )
            .group_by(file_max_score_subq.c.defense_group_id)
        ).subquery()

        # Subquery: For each group, get the minimal anonym_id among files with minimal attack_score
        min_file_id_subq = (
            db.session.query(
                file_max_score_subq.c.defense_group_id,
                func.min(file_max_score_subq.c.anonym_id).label('minimal_attack_file_id')
            )
            .join(min_file_score_subq,
                  (min_file_score_subq.c.defense_group_id == file_max_score_subq.c.defense_group_id) &
                  (min_file_score_subq.c.attack_score == file_max_score_subq.c.max_score)
            )
            .group_by(file_max_score_subq.c.defense_group_id)
        ).subquery()

        # Main query: Join to get group name, attack_score, and minimal_attack_file info
        results = (
            db.session.query(
                file_max_score_subq.c.defense_group_id.label('attacked_group_id'),
                GroupUserModel.name.label('attacked_group_name'),
                file_max_score_subq.c.max_score.label('attack_score'),
                file_max_score_subq.c.anonym_id.label('minimal_attack_file_id'),
                file_max_score_subq.c.anonym_name.label('minimal_attack_file_name')
            )
            .join(min_file_score_subq,
                  (min_file_score_subq.c.defense_group_id == file_max_score_subq.c.defense_group_id) &
                  (min_file_score_subq.c.attack_score == file_max_score_subq.c.max_score)
            )
            .join(min_file_id_subq,
                  (min_file_id_subq.c.defense_group_id == file_max_score_subq.c.defense_group_id) &
                  (min_file_id_subq.c.minimal_attack_file_id == file_max_score_subq.c.anonym_id)
            )
            .join(GroupUserModel, GroupUserModel.id == file_max_score_subq.c.defense_group_id)
        ).all()

        response = []
        for row in results:
            response.append({
                "attacked_group_id": row.attacked_group_id,
                "attacked_group_name": row.attacked_group_name,
                "attack_score": row.attack_score,
                "minimal_attack_file": {
                    "id": row.minimal_attack_file_id,
                    "name": row.minimal_attack_file_name
                }
            })
        return ResponseBuilder().success(
            message="Fetched attacked groups and minimal attack info.",
            data=response,
            status_code=HTTPStatus.OK
        ).build()

@blp.route("/files/<int:group_id_attack>/<int:group_id_defense>")
class AttackFilesByGroup(MethodView):
    """
    Get all files of a group that were attacked by another group, with max attack score per file.
    """
    def get(self, group_id_attack, group_id_defense):
        results = (
            db.session.query(
                AnonymModel.id,
                AnonymModel.name,
                func.max(AttackModel.score).label('max_attack_score')
            )
            .join(AttackModel, AttackModel.anonym_id == AnonymModel.id)
            .filter(
                AttackModel.group_id == group_id_attack,      # attacker
                AnonymModel.group_id == group_id_defense      # defender
            )
            .group_by(AnonymModel.id, AnonymModel.name)
            .all()
        )

        response = []
        for row in results:
            response.append({
                "file_id": row.id,
                "file_name": row.name,
                "max_attack_score": row.max_attack_score
            })
        return ResponseBuilder().success(
            message="Fetched attacked files and max attack score.",
            data=response,
            status_code=HTTPStatus.OK
        ).build()


