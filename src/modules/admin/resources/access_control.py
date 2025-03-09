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
from src.modules.auth.schemas import UserSchema, GroupUserSchema

from http import HTTPStatus
from sqlalchemy import select
from src.constants.app_msg import *
from src.constants.admin import *
from src.common.pagination import PageNumberPagination

from openapi import *
from src.modules.admin.resources import admin_blp

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
        serialized_items = InviteKeySchema(many=True).dump(items)

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

@admin_blp.route("/user")
class UserList(MethodView):
    """Handles retrieving a list of users with pagination."""
    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.OK, UserSchema(many=True))
    @admin_blp.doc(**user_list_doc)
    def get(self):
        """Retrieves a paginated list of users."""
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)
        count = request.args.get('count', type=str)

        if count is not None:
            count = count.lower() == 'true'

        users = select(UserModel)

        paginator = PageNumberPagination(
            select=users,  
            page=page,
            per_page=per_page,
            count=count
        )

        result = paginator.paginate()
        items = result['data']
        meta = result['meta']

        serialized_items = UserSchema(many=True).dump(items)

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