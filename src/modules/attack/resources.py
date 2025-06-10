from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, jsonify
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
    @jwt_required()
    def get(self):
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
        return jsonify(result), HTTPStatus.OK

@blp.route("/<int:group_id>/published-files")
class GroupPublishedFiles(MethodView):
    @jwt_required()
    def get(self, group_id):
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
        return jsonify(result), HTTPStatus.OK

@blp.route("/<int:anonym_id>/my-score")
class MyAttackScore(MethodView):
    @jwt_required()
    def get(self, anonym_id):
        user_id = get_jwt_identity()
        user = db.session.get(UserModel, user_id)
        my_group_id = user.group_id if user else None

        attack = (
            db.session.query(AttackModel)
            .filter_by(anonym_id=anonym_id, group_id=my_group_id)
            .order_by(AttackModel.id.desc())
            .first()
        )
        score = attack.score if attack else 0
        return jsonify({"score": score}), HTTPStatus.OK

@blp.route("/<int:anonym_id>/my-attacks")
class MyAttackHistory(MethodView):
    @jwt_required()
    def get(self, anonym_id):
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
        return jsonify(result), HTTPStatus.OK


