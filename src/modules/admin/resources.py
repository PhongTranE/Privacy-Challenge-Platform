from src.extensions import db 
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from src.common.decorators import role_required
from src.modules.admin.services import generate_invite_key

from src.modules.admin.models import InviteKey
from src.models.user import UserModel

from flask import jsonify
from src.modules.admin.schemas import InviteKeySchema
from src.modules.auth.schemas import UserSchema

from http import HTTPStatus
from sqlalchemy import select
from src.constants.messages import *
from src.constants.admin import *


blp = Blueprint("admin", __name__, description="Admin Management")

@blp.route("/invite")
class InviteUser(MethodView):

    @role_required([ADMIN_ROLE])
    @blp.response(HTTPStatus.CREATED, InviteKeySchema)
    def post(self):
        """Generate a new invite key """
        new_key = generate_invite_key()

        MAX_RETRIES = 10  # Set a reasonable limit
        attempt = 0

        while db.session.get(InviteKey, new_key) and attempt < MAX_RETRIES:
            new_key = generate_invite_key()
            attempt += 1

        if attempt == MAX_RETRIES:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message=GENERATE_INVITE_KEY_ERROR)

        invite_key = InviteKey(key=new_key)
        db.session.add(invite_key)
        db.session.commit()

        return invite_key
    
    @role_required([ADMIN_ROLE])
    @blp.response(HTTPStatus.OK, InviteKeySchema(many=True))
    def get(self):
        invite_keys = db.session.execute(select(InviteKey)).scalars().all()
        return invite_keys

@blp.route("/invite/<string:key>")
class InviteKeyRemove(MethodView):

    @role_required([ADMIN_ROLE])
    def delete(self, key):
        invite_key = db.session.get(InviteKey, key)
        if not invite_key:
            abort(HTTPStatus.NOT_FOUND, message=INVITE_KEY_NOT_FOUND)
        db.session.delete(invite_key)
        db.session.commit()
        return jsonify({"message": INVITE_KEY_DELETED}), HTTPStatus.OK

@blp.route("/user")
class UserList(MethodView):

    @role_required([ADMIN_ROLE])
    @blp.response(HTTPStatus.OK, UserSchema(many=True))
    def get(self):
        users = db.session.execute(select(UserModel)).scalars().all()
        return users

@blp.route("/user/<int:user_id>")
class User(MethodView):

    @role_required([ADMIN_ROLE])
    def delete(self, user_id):
        user = db.session.get(UserModel, user_id)
        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": USER_DELETED}), HTTPStatus.OK

