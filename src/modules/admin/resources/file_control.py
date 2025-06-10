from flask.views import MethodView
from flask_smorest import abort
from src.common.decorators import role_required
from flask import request, current_app
from src.constants.admin import *
from src.constants.app_msg import *
from http import HTTPStatus
from src.core.services.file_manager import FileManager
from flask import jsonify
from src.modules.admin.resources import admin_blp
from src.modules.admin.models import RawFileModel
from src.extensions import db
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import IntegrityError
from src.common.response_builder import ResponseBuilder
import time
import os
import re
from flask import send_file
from src.modules.auth.models import GroupUserModel
from src.modules.admin.services import get_group_files
from src.modules.admin.schemas import GroupFileSchema
from src.modules.anonymisation.models import AnonymModel
from src.modules.attack.models import AttackModel
from flask import after_this_request

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

def extract_base_filename(filename):
    # Loại bỏ _timestamp hoặc (n) trước .zip
    return re.sub(r'(_\d+)?(\(\d+\))?\.zip$', '', filename)

def get_next_available_filename(base, ext, upload_dir):
    pattern = re.compile(rf'^{re.escape(base)}(?:\((\d+)\))?{re.escape(ext)}$')
    existing = [f for f in os.listdir(upload_dir) if pattern.match(f)]
    numbers = [int(pattern.match(f).group(1) or 0) for f in existing]
    next_num = 1
    while f"{base}({next_num}){ext}" in existing:
        next_num += 1
    return f"{base}({next_num}){ext}"

@admin_blp.route("/upload")
class OriginalFile(MethodView):
    @role_required([ADMIN_ROLE])
    def post(self):
        if "file" not in request.files:
            abort(HTTPStatus.BAD_REQUEST, message=NO_FILE_UPLOADED)

        file = request.files["file"]
        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            abort(HTTPStatus.BAD_REQUEST, message="File size exceeds 50MB limit")

        # Validate extension
        allowed_ext = ".zip"
        original_filename = file.filename
        name, ext = os.path.splitext(original_filename)
        if ext != allowed_ext:
            abort(HTTPStatus.BAD_REQUEST, message="Only ZIP files are allowed")

        # Làm sạch tên file
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        filename = f"{safe_name}{ext}"

        file_manager = FileManager(upload_dir="original_files", allowed_extensions={"zip"})
        upload_dir = file_manager.upload_dir

        overwrite = request.form.get("overwrite") == "true"
        auto_rename = request.form.get("auto_rename") == "true"

        # Kiểm tra duplicate theo filename đã làm sạch
        existing_file = RawFileModel.query.filter(
            RawFileModel.filename == filename
        ).first()

        if existing_file:
            if overwrite:
                # Xóa file cũ trên disk và DB
                try:
                    old_file_path = existing_file.file_path
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                except Exception:
                    pass
                db.session.delete(existing_file)
                db.session.commit()
            elif auto_rename:
                # Sinh tên mới: upload(1).zip, upload(2).zip, ...
                i = 1
                new_filename = f"{safe_name}({i}){ext}"
                while RawFileModel.query.filter(RawFileModel.filename == new_filename).first():
                    i += 1
                    new_filename = f"{safe_name}({i}){ext}"
                filename = new_filename
            else:
                abort(HTTPStatus.CONFLICT, message="File name already exists")

        try:
            file_path = file_manager.save_file(file, filename=filename)
            extracted_file_path = file_manager.unzip_file(file_path)
            current_app.config["ORIGINAL_FILE_PATH"] = extracted_file_path

            # Deactivate all existing files
            RawFileModel.query.update({"is_active": False})
            creator_id = get_jwt_identity()
            file_model = RawFileModel(
                original_filename=original_filename,
                filename=filename,
                file_path=file_path,
                creator_id=creator_id,
                is_active=True
            )
            db.session.add(file_model)
            db.session.commit()

            return (
                ResponseBuilder()
                .success(
                    message=FILE_UPLOADED_SUCESS,
                    data={
                        "file_path": file_path,
                        "extracted_file_path": extracted_file_path,
                        "file_id": file_model.id,
                        "filename": filename
                    },
                    status_code=HTTPStatus.CREATED
                )
                .build()
            )
        except IntegrityError:
            db.session.rollback()
            abort(HTTPStatus.BAD_REQUEST, message="File already exists, please try again with a different file.")
        except Exception as e:
            db.session.rollback()
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message=INTERNAL_SERVER_ERROR)

@admin_blp.route("/files")
class FileList(MethodView):
    @role_required([ADMIN_ROLE])
    def get(self):
        try:
            files = RawFileModel.query.order_by(RawFileModel.uploaded_at.desc()).all()
            return (
                ResponseBuilder()
                .success(
                    message="File list fetched successfully",
                    data=[
                        {
                            "id": file.id,
                            "filename": file.filename,
                            "uploaded_at": file.uploaded_at.isoformat(),
                            "is_active": file.is_active,
                            "creator_id": file.creator_id
                        } for file in files
                    ],
                    status_code=HTTPStatus.OK
                )
                .build()
            )
        except Exception as e:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Get file list failed")

@admin_blp.route("/files/<int:file_id>")
class FileResource(MethodView):
    @role_required([ADMIN_ROLE])
    def delete(self, file_id):
        file = RawFileModel.query.get_or_404(file_id)
        try:
            # Delete file from filesystem
            file_manager = FileManager(upload_dir="original_files")
            file_manager.delete_file(file.file_path)
            # Delete from database
            db.session.delete(file)
            db.session.commit()
            return (
                ResponseBuilder()
                .success(
                    message=FILE_DELETED_SUCCESS,
                    status_code=HTTPStatus.OK
                )
                .build()
            )
        except Exception as e:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Delete failed")

@admin_blp.route("/files/<int:file_id>/activate")
class FileActivateResource(MethodView):
    @role_required([ADMIN_ROLE])
    def patch(self, file_id):
        file = RawFileModel.query.get_or_404(file_id)
        try:
            # Nếu file đã active thì chuyển thành inactive (toggle off)
            if file.is_active:
                file.is_active = False
            else:
                # Nếu file chưa active thì active nó và inactive tất cả file khác
                RawFileModel.query.update({"is_active": False})
                file.is_active = True
            db.session.commit()
            return (
                ResponseBuilder()
                .success(
                    message="File status updated successfully",
                    data={
                        "id": file.id,
                        "is_active": file.is_active
                    },
                    status_code=HTTPStatus.OK
                )
                .build()
            )
        except Exception as e:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Activate failed")
    

@admin_blp.route("/group_user/<int:group_user_id>/files")
class GroupUserFiles(MethodView):
    """Handles retrieving group files."""
    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.OK, GroupFileSchema(many=True))
    def get(self, group_user_id):
        """Retrieves files (anonymous and attack) of a group."""
        file_type = request.args.get('type', type=str)  # 'anonymous', 'attack', or None for all
        limit = request.args.get('limit', default=20, type=int)
        
        group = db.session.get(GroupUserModel, group_user_id)
        if not group:
            abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)
        
        files = get_group_files(group_user_id, file_type, limit)
        return ResponseBuilder().success(
            message="Group files retrieved successfully",
            data=files
        ).build()


@admin_blp.route("/group_user/<int:group_user_id>/files/<string:file_type>/<int:file_id>/download")
class GroupUserFileDownload(MethodView):
    """Handles file download for group files."""
    @role_required([ADMIN_ROLE])
    def get(self, group_user_id, file_type, file_id):
        """Downloads a file (anonymous or attack) from a group."""

        
        # Verify group exists
        group = db.session.get(GroupUserModel, group_user_id)
        if not group:
            abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)
        
        file_path = None
        filename = None
        
        if file_type == 'anonymous':
            anonym = db.session.get(AnonymModel, file_id)
            if not anonym or anonym.group_id != group_user_id:
                abort(HTTPStatus.NOT_FOUND, message="Anonymous file not found")
            file_path = anonym.file_link + ".csv"
            filename = f"{anonym.name}_anonymous.csv"
            
        elif file_type == 'attack':
            attack = db.session.get(AttackModel, file_id)
            if not attack or attack.group_id != group_user_id:
                abort(HTTPStatus.NOT_FOUND, message="Attack file not found")
            file_path = attack.file
            ext = os.path.splitext(file_path)[1] 
            filename = f"attack_{attack.id}{ext}"
        else:
            abort(HTTPStatus.BAD_REQUEST, message="Invalid file type")
        
        if not file_path or not os.path.exists(file_path):
            abort(HTTPStatus.NOT_FOUND, message="File not found on disk")
        
        @after_this_request
        def add_header(response):
            response.headers.add("Access-Control-Expose-Headers", "Content-Disposition")
            return response
        return send_file(file_path, as_attachment=True, download_name=filename)


@admin_blp.route("/group_user/<int:group_user_id>/files/<string:file_type>/<int:file_id>")
class GroupUserFileManagement(MethodView):
    """Handles file management for group files."""
    @role_required([ADMIN_ROLE])
    def delete(self, group_user_id, file_type, file_id):
        """Deletes a file (anonymous or attack) from a group."""
        
        # Verify group exists
        group = db.session.get(GroupUserModel, group_user_id)
        if not group:
            abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)
        
        try:
            if file_type == 'anonymous':
                anonym = db.session.get(AnonymModel, file_id)
                if not anonym or anonym.group_id != group_user_id:
                    abort(HTTPStatus.NOT_FOUND, message="Anonymous file not found")
                
                # Delete physical files
                if anonym.file_link and os.path.exists(anonym.file_link):
                    os.remove(anonym.file_link)
                if anonym.footprint_file and os.path.exists(anonym.footprint_file):
                    os.remove(anonym.footprint_file)
                if anonym.shuffled_file and os.path.exists(anonym.shuffled_file):
                    os.remove(anonym.shuffled_file)
                
                # Delete database record
                db.session.delete(anonym)
                db.session.commit()
                
                return jsonify({"message": "Anonymous file deleted successfully"}), HTTPStatus.OK
                
            elif file_type == 'attack':
                attack = db.session.get(AttackModel, file_id)
                if not attack or attack.group_id != group_user_id:
                    abort(HTTPStatus.NOT_FOUND, message="Attack file not found")
                
                # Delete physical file
                if attack.file and os.path.exists(attack.file):
                    os.remove(attack.file)
                
                # Delete database record
                db.session.delete(attack)
                db.session.commit()
                
                return jsonify({"message": "Attack file deleted successfully"}), HTTPStatus.OK
            else:
                abort(HTTPStatus.BAD_REQUEST, message="Invalid file type")
                
        except Exception as e:
            db.session.rollback()
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message=f"Failed to delete file: {str(e)}")