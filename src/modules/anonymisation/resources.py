from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, jsonify, send_file, after_this_request
from http import HTTPStatus
from .services import AnonymService
from .models import AnonymModel
from src.common.decorators import group_required  
from src.extensions import db
from flask_jwt_extended import jwt_required
from src.modules.admin.models import RawFileModel

blp = Blueprint("anonymisation_func", __name__, description="Anonymisation Management")

@blp.route("/upload")
class AnonymUpload(MethodView):
    @jwt_required()
    def post(self):
        """Handles file upload and triggers anonymization."""
        if "file" not in request.files:
            abort(HTTPStatus.BAD_REQUEST, message="No file uploaded.")

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

        return jsonify({
            "status": anonym.status,
            "utility_score": anonym.utility,
            "naive_attack_score": anonym.naive_attack,
            "is_published": anonym.is_published
        }), HTTPStatus.OK


@blp.route("/toggle-publish/<int:anonym_id>")
class AnonymTogglePublish(MethodView):
    """Allows group members to publish or unpublish an anonymization entry."""

    @group_required()
    def patch(self, anonym_id):
        anonym = db.session.get(AnonymModel, anonym_id)

        if not anonym:
            abort(HTTPStatus.NOT_FOUND, message="Anonymization not found.")
        
        if anonym.status != "completed":
            abort(HTTPStatus.BAD_REQUEST, message="Anonymization must be 'completed' before modifying publish status.")

        # Toggle publish state
        anonym.is_published = not anonym.is_published
        db.session.commit()

        return jsonify({
            "message": f"Anonymization {anonym_id} is now {'published' if anonym.is_published else 'unpublished'}.",
            "is_published": anonym.is_published
        }), HTTPStatus.OK


def make_response(data=None, message="Success", status="success", error=None):
    resp = {
        "status": status,
        "message": message,
        "data": data
    }
    if error:
        resp["error"] = error
    return jsonify(resp)


@blp.route("/check-active-rawfile")
class CheckActiveRawFile(MethodView):
    def get(self):
        active_file = RawFileModel.query.filter_by(is_active=True).first()
        if active_file:
            return make_response(
                data=None,
                message="There is an active raw file.",
                status="success"
            ), HTTPStatus.OK
        else:
            return make_response(
                data=None,
                message="No active raw file found.",
                status="error",
                error="NO_ACTIVE_RAWFILE"
            ), HTTPStatus.NOT_FOUND


@blp.route("/download-rawfile")
class DownloadRawFile(MethodView):
    def get(self):
        active_file = RawFileModel.query.filter_by(is_active=True).first()
        if not active_file:
            return make_response(
                data=None,
                message="No active raw file to download.",
                status="error",
                error="NO_ACTIVE_RAWFILE"
            ), HTTPStatus.NOT_FOUND

        import os
        if not os.path.exists(active_file.file_path):
            return make_response(
                data=None,
                message="Raw file not found on server.",
                status="error",
                error="FILE_NOT_FOUND"
            ), HTTPStatus.NOT_FOUND

        @after_this_request
        def add_header(response):
            response.headers.add("Access-Control-Expose-Headers", "Content-Disposition")
            return response

        return send_file(
            active_file.file_path,
            as_attachment=True,
            download_name="rawfile.zip",
            mimetype="application/zip"
        )
