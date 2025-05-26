from src.extensions import db 
from flask.views import MethodView
from flask import request
from flask_smorest import abort
from src.common.decorators import role_required
from src.modules.admin.services import generate_invite_key

from src.modules.admin.models import InviteKeyModel
from src.modules.auth.models import UserModel, GroupUserModel

from flask import jsonify
from src.modules.admin.schemas import InviteKeySchema
from src.modules.auth.schemas import UserLoginSchema, GroupUserSchema, ResetPasswordSchema

from http import HTTPStatus
from sqlalchemy import select, or_
from src.constants.app_msg import *
from src.constants.admin import *
from src.common.pagination import PageNumberPagination

from openapi import *
from src.modules.admin.resources import admin_blp
from src.modules.admin.services import is_invite_key_expired
from src.modules.auth.services import hash_password, validate_password_match, validate_password
from marshmallow import ValidationError
from marshmallow import fields, Schema


@admin_blp.route("/invite")
class InviteUser(MethodView):
    """Handles invite key management for user registration."""
    
    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.CREATED, InviteKeySchema)

    def post(self):
        """Generates a new unique invite key for user registration."""
        new_key = generate_invite_key()

        MAX_RETRIES = 10 
        attempt = 0

        while db.session.get(InviteKeyModel, new_key) and attempt < MAX_RETRIES:
            new_key = generate_invite_key()
            attempt += 1

        if attempt == MAX_RETRIES:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message=GENERATE_INVITE_KEY_ERROR)

        invite_key = InviteKeyModel(key=new_key)
        db.session.add(invite_key)
        db.session.commit()
        
        invite_key.is_expired = is_invite_key_expired(invite_key)

        return invite_key
    
    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.OK, InviteKeySchema(many=True))
    @admin_blp.doc(**invite_key_list_doc)
    def get(self):
        """Retrieves a paginated list of all active invite keys."""
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)
        count = request.args.get('count', type=str)

        # Convert 'count' parameter to boolean if provided
        if count is not None:
            count = count.lower() == 'true'

        invite_keys = select(InviteKeyModel)

        paginator = PageNumberPagination(
            select=invite_keys,  
            page=page,
            per_page=per_page,
            count=count
        )

        result = paginator.paginate()
        items = result['data']
        meta = result['meta']

        # Serialize items using the schema
        # serialized_items = InviteKeySchema(many=True).dump(items)

        serialized_items = []
        for item in items:
            data = InviteKeySchema().dump(item)
            data['is_expired'] = is_invite_key_expired(item)
            serialized_items.append(data)

        # Return a JSON response with data and metadata
        return jsonify({
            'data': serialized_items,
            'meta': meta
        })

@admin_blp.route("/invite/<string:key>")
class InviteKeyRemove(MethodView):
    """Handles deleting an invite key."""
    @role_required([ADMIN_ROLE])
    def delete(self, key):
        """Deletes an invite key if it exists."""
        invite_key = db.session.get(InviteKeyModel, key)
        if not invite_key:
            abort(HTTPStatus.NOT_FOUND, message=INVITE_KEY_NOT_FOUND)
        db.session.delete(invite_key)
        db.session.commit()
        return jsonify({"message": INVITE_KEY_DELETED}), HTTPStatus.OK

@admin_blp.route("/invite/expired")
class ExpiredInviteKeyRemove(MethodView):
    """Handles deleting all expired invite keys."""
    @role_required([ADMIN_ROLE])
    def delete(self):
        expired_keys = db.session.query(InviteKeyModel).all()
        count = 0
        for key in expired_keys:
            if is_invite_key_expired(key):
                db.session.delete(key)
                count += 1
        db.session.commit()
        return jsonify({"message": f"Deleted {count} expired invite keys."}), HTTPStatus.OK

@admin_blp.route("/user")
class UserList(MethodView):
    """Handles retrieving a list of users with pagination."""
    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.OK, UserLoginSchema(many=True))
    @admin_blp.doc(**user_list_doc)
    def get(self):
        """Retrieves a paginated list of users."""
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)
        count = request.args.get('count', type=str)
        search = request.args.get('search', type=str)

        if count is not None:
            count = count.lower() == 'true'

        users = select(UserModel)

        if search:
            search_pattern = f"%{search}%"
            users = users.where(
                or_(
                    UserModel.username.ilike(search_pattern),
                    UserModel.email.ilike(search_pattern),
                    UserModel.group.has(GroupUserModel.name.ilike(search_pattern))
                )
            )

        paginator = PageNumberPagination(
            select=users,  
            page=page,
            per_page=per_page,
            count=count
        )

        result = paginator.paginate()
        items = result['data']
        meta = result['meta']

        serialized_items = UserLoginSchema(many=True).dump(items)

        return jsonify({
            'data': serialized_items,
            'meta': meta
        })

@admin_blp.route("/user/<int:user_id>")
class User(MethodView):
    """Handles deleting a user from the system."""
    @role_required([ADMIN_ROLE])
    def delete(self, user_id):
        """Deletes a user if they exist."""
        user = db.session.get(UserModel, user_id)
        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": USER_DELETED}), HTTPStatus.OK


@admin_blp.route("/user/<int:user_id>/password")
class AdminUserPassword(MethodView):
    @role_required([ADMIN_ROLE])
    @admin_blp.arguments(
        Schema.from_dict({
            "new_password": fields.Str(required=True, validate=validate_password)
        })()
    )
    def put(self, password_data, user_id):
        user = db.session.get(UserModel, user_id)
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found!",
            }), 404
        try:
            validate_password(password_data["new_password"])
            user.password = password_data["new_password"]
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": "Password updated successfully!",
            }), 200
        except ValidationError as ve:
            return jsonify({
                "status": "error",
                "message": { "json": ve.messages },
            }), 400
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e),
            }), 500


@admin_blp.route("/group_user")
class GroupUserList(MethodView):
    """Handles retrieving a list of group_users with pagination."""
    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.OK, GroupUserSchema(many=True))
    def get(self):
        """Retrieves a paginated list of group_users."""
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)
        count = request.args.get('count', type=str)

        if count is not None:
            count = count.lower() == 'true'

        users = select(GroupUserModel)

        paginator = PageNumberPagination(
            select=users,  
            page=page,
            per_page=per_page,
            count=count
        )

        result = paginator.paginate()
        items = result['data']
        meta = result['meta']

        serialized_items = GroupUserSchema(many=True).dump(items)

        return jsonify({
            'data': serialized_items,
            'meta': meta
        })