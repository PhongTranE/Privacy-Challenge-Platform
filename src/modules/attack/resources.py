from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, jsonify
from http import HTTPStatus
from src.extensions import db
from flask_jwt_extended import get_jwt, jwt_required
from src.modules.attack.services import AttackService

blp = Blueprint("attack_func", __name__, description="Attack Management")

@blp.route("/<int:anonym_id>/upload")
class AttackUpload(MethodView):
    @jwt_required()
    def post(self, anonym_id):
        if "file" not in request.files:
            abort(HTTPStatus.BAD_REQUEST, message="No file uploaded.")

        file = request.files["file"]

        jwt_claims = get_jwt()
        user_group = jwt_claims.get("group", None) 

        return AttackService.process_attack(file, anonym_id, user_group)


