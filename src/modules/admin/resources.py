from src.extensions import db 
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from src.common.decorators import role_required
from src.modules.admin.services import generate_invite_key
from src.modules.admin.models import InviteKey
from flask import jsonify
from src.modules.admin.schemas import InviteKeySchema
from http import HTTPStatus
from sqlalchemy import select
from src.constants.messages import *

blp = Blueprint("admin", __name__, description="Admin Management")

@blp.route("/invite")
class InviteUser(MethodView):

    @role_required(["Administrator"])
    @blp.response(HTTPStatus.CREATED, InviteKeySchema)
    def post(self):
        """Generate a new invite key """
        new_key = generate_invite_key()

        while db.session.get(InviteKey, new_key):
            new_key = generate_invite_key()
        
        invite_key = InviteKey(key=new_key)
        db.session.add(invite_key)
        db.session.commit()

        return invite_key
    
    @role_required(["Administrator"])
    @blp.response(HTTPStatus.OK, InviteKeySchema(many=True))
    def get(self):
        invite_keys = db.session.execute(select(InviteKey)).scalars().all()
        return invite_keys

@blp.route("/invite/<string:key>")
class InviteKeyRemove(MethodView):

    @role_required(["Administrator"])
    def delete(self, key):
        invite_key = db.session.get(InviteKey, key)
        if not invite_key:
            abort(HTTPStatus.NOT_FOUND, message=INVITE_KEY_NOT_FOUND)
        db.session.delete(invite_key)
        db.session.commit()
        return jsonify({"message": INVITE_KEY_DELETED}), HTTPStatus.OK


