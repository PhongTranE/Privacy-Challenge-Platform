from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, send_file, after_this_request
from http import HTTPStatus
from .services import AnonymService
from .models import AnonymModel
from src.common.decorators import group_required  
from src.extensions import db
from flask_jwt_extended import jwt_required, get_jwt
from src.modules.admin.models import RawFileModel
from src.common.response_builder import ResponseBuilder
from src.constants.app_msg import *
from src.modules.anonymisation.services import validate_submission_limit
from src.modules.admin.services import group_not_banned_required
from src.modules.attack.models import AttackModel
from src.modules.auth.models import GroupUserModel

blp = Blueprint("anonymisation_func", __name__, description="Anonymisation Management")

@blp.route("/upload")
class AnonymUpload(MethodView):
    """Handles file upload and triggers anonymization."""
    @jwt_required()
    @group_not_banned_required()
    def post(self):
        """Handles file upload and triggers anonymization."""
        claims = get_jwt()
        group_id = claims.get('group')
        validation_error = validate_submission_limit(group_id)
        if validation_error:
            abort(HTTPStatus.BAD_REQUEST, message=validation_error)

        if "file" not in request.files:
            abort(HTTPStatus.BAD_REQUEST, message=NO_FILE_UPLOADED)

        file = request.files["file"]
        response, status_code = AnonymService.process_anonymization(file)

        return response, status_code

@blp.route("/result/<int:anonym_id>") 
class AnonymResult(MethodView):
    """Fetches the anonymization result for a given file."""
    @jwt_required()
    def get(self, anonym_id):
        """Retrieve anonymization status and results from the database."""
        anonym = db.session.get(AnonymModel, anonym_id)  

        if not anonym:
            abort(HTTPStatus.NOT_FOUND, message="Anonymization result not found.")

        return (
            ResponseBuilder()
            .success(
                message="Anonymization result fetched successfully",
                data={
                    "status": anonym.status,
                    "utility_score": anonym.utility,
                    "naive_attack_score": anonym.naive_attack,
                    "is_published": anonym.is_published
                },
                status_code=HTTPStatus.OK
            )
            .build()
        )


@blp.route("/toggle-publish/<int:anonym_id>")
class AnonymTogglePublish(MethodView):
    """Allows group members to publish or unpublish an anonymization entry."""

    @group_required()
    @group_not_banned_required()
    def patch(self, anonym_id):
        anonym = db.session.get(AnonymModel, anonym_id)

        if not anonym:
            abort(HTTPStatus.NOT_FOUND, message="Anonymization not found.")
        
        if anonym.status != "completed":
            abort(HTTPStatus.BAD_REQUEST, message="Anonymization must be 'completed' before modifying publish status.")

        # Toggle publish state
        anonym.is_published = not anonym.is_published
        db.session.commit()

        return (
            ResponseBuilder()
            .success(
                message=f"Anonymization {anonym_id} is now {'published' if anonym.is_published else 'unpublished'}.",
                data={
                    "is_published": anonym.is_published
                },
                status_code=HTTPStatus.OK
            )
            .build()
        )


@blp.route("/list")
class AnonymList(MethodView):
    @jwt_required()
    def get(self):
        """Retrieve anonymisation list for the current group."""
        claims = get_jwt()
        group_id = claims.get('group')
        if not group_id:
            abort(HTTPStatus.FORBIDDEN, message="User must be part of a group.")
        files = (
            db.session.query(AnonymModel)
            .filter_by(group_id=group_id)
            .order_by(AnonymModel.id.desc())
            .all()
        )
        data = [
            {
                "id": f.id,
                "name": f.name,
                "status": f.status,
                "utility": f.utility,
                "naive_attack": f.naive_attack,
                "is_published": f.is_published,
                "created_at": str(getattr(f, "created_at", "")),
            }
            for f in files
        ]
        return ResponseBuilder().success(
            message="Fetched anonymisation list successfully",
            data=data,
            status_code=HTTPStatus.OK
        ).build()

@blp.route("/check-active-rawfile")
class CheckActiveRawFile(MethodView):
    def get(self):
        active_file = RawFileModel.query.filter_by(is_active=True).first()
        if active_file:
            return (
                ResponseBuilder()
                .success(
                    message="There is an active raw file.",
                    status_code=HTTPStatus.OK
                )
                .build()
            )
        else:
            abort(HTTPStatus.NOT_FOUND, message="No active raw file found.")


@blp.route("/download-rawfile")
class DownloadRawFile(MethodView):
    def get(self):
        active_file = RawFileModel.query.filter_by(is_active=True).first()
        if not active_file:
            abort(HTTPStatus.NOT_FOUND, message="No active raw file to download.")

        import os
        if not os.path.exists(active_file.file_path):
            abort(HTTPStatus.NOT_FOUND, message="Raw file not found on server.")

        @after_this_request
        def add_header(response):
            response.headers.add("Access-Control-Expose-Headers", "Content-Disposition")
            return response

        return send_file(
            active_file.file_path,
            as_attachment=True,
            download_name="rawFile.zip",
            mimetype="application/zip"
        )
