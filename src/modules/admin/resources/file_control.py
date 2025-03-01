from flask.views import MethodView
from flask_smorest import abort
from src.common.decorators import role_required
from flask import request 
from src.constants.admin import *
from src.constants.messages import *
from http import HTTPStatus
from src.core.services.file_manager import FileManager
from flask import jsonify
from src.modules.admin.resources import admin_blp

@admin_blp.route("/upload")
class OriginalFile(MethodView):
    @role_required([ADMIN_ROLE])
    def post(self):
        if "file" not in request.files:
            abort(HTTPStatus.BAD_REQUEST, message=NO_FILE_UPLOADED)

        file_manager = FileManager(upload_dir="original_files", allowed_extensions={"zip"})
        file = request.files["file"]
        try: 
            filename= f"{ORIGINAL_FILENAME}.zip"
            file_path = file_manager.save_file(file, filename=filename)
            extracted_file_path = file_manager.unzip_file(file_path)
            return jsonify({
                "message": FILE_UPLOADED_SUCESS,
                "file_path": file_path,
                "extracted_file_path": extracted_file_path,
            }), HTTPStatus.CREATED
        
        except Exception as e:
            abort(HTTPStatus.BAD_REQUEST, message=str(e))
    
