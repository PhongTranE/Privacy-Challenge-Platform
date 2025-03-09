from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, jsonify
from http import HTTPStatus
from .services import AnonymService
from .models import AnonymModel

from src.extensions import db

blp = Blueprint("anonymisation_func", __name__, description="Anonymisation Management")

@blp.route("/upload")
class AnonymUpload(MethodView):
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

            
