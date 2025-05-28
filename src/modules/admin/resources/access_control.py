from src.extensions import db 
from flask.views import MethodView
from flask import request
from flask_smorest import abort
from src.common.decorators import role_required
from src.common.response_builder import ResponseBuilder
from src.modules.admin.services import generate_invite_key, get_group_detail, update_group_name

from src.modules.admin.models import InviteKeyModel
from src.modules.auth.models import UserModel, GroupUserModel
from src.modules.anonymisation.models import AnonymModel
from src.modules.attack.models import AttackModel
from flask import jsonify
from src.modules.admin.schemas import InviteKeySchema, GroupDetailSchema, UpdateGroupNameSchema
from src.modules.auth.schemas import UserLoginSchema, GroupUserSchema

from http import HTTPStatus
from sqlalchemy import select, or_, func
from sqlalchemy.exc import SQLAlchemyError
from src.constants.app_msg import *
from src.constants.admin import *
from src.common.pagination import PageNumberPagination

from openapi import *
from src.modules.admin.resources import admin_blp
from src.modules.admin.services import is_invite_key_expired
from src.modules.auth.services import validate_password
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
        
        group_id = user.group_id

        db.session.delete(user)
        db.session.commit()

        # If user has a group, check if there are any users left in the group
        if group_id:
            remaining = (
                db.session.query(UserModel)
                .filter(UserModel.group_id == group_id)
                .count()
            )
            if remaining == 0:
                group = db.session.get(GroupUserModel, group_id)
                if group:
                    group_name = group.name
                    db.session.delete(group)
                    db.session.commit()
                    group_deleted_info = {
                        "group_deleted": True,
                        "group_id": group_id,
                        "group_name": group_name
                    }
        data = {"group_deleted": False}
        if group_deleted_info:
            data.update(group_deleted_info)

        return (
            ResponseBuilder()
            .success(message=USER_DELETED, data=data, status_code=HTTPStatus.OK)
            .build()
            )


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
            return jsonify({"message": USER_NOT_FOUND}), HTTPStatus.NOT_FOUND
        try:
            validate_password(password_data["new_password"])
            user.password = password_data["new_password"]
            db.session.commit()
            return jsonify({"message": PASSWORD_RESET_SUCCESS}), HTTPStatus.OK
        except ValidationError as ve:
            return jsonify({"message": ve.messages}), HTTPStatus.BAD_REQUEST
        except Exception as e:
            return jsonify({"message": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


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
        search = request.args.get('search', type=str)

        if count is not None:
            count = count.lower() == 'true'

        per_page = per_page or 5
        page = page or 1

        if count:
            count_stmt = select(func.count()).select_from(GroupUserModel)

            if search:
                search_pattern = f"%{search}%"
                count_stmt = count_stmt.where(
                    or_(
                        GroupUserModel.name.ilike(search_pattern),
                        GroupUserModel.users.any(UserModel.username.ilike(search_pattern))
                    )
                )

            total_items = db.session.execute(count_stmt).scalar_one()
            total_pages = (total_items + per_page - 1) // per_page
        else:
            total_items = None
            total_pages = None

        stmt = (
            select(GroupUserModel, func.count(UserModel.id).label("member_count"))
            .outerjoin(UserModel, GroupUserModel.id == UserModel.group_id)
            .group_by(GroupUserModel.id)
        )

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    GroupUserModel.name.ilike(search_pattern),
                    GroupUserModel.users.any(UserModel.username.ilike(search_pattern)),
                )
            )

        paginator = PageNumberPagination(
            select=stmt,  
            page=page,
            per_page=per_page,
            count=False,
            as_tuple=True
        )

        result = paginator.paginate()
        items = result['data']
        meta = result['meta']
        meta['total_items'] = total_items
        meta['total_pages'] = total_pages

        serialized_items = []
        for group, member_count in items:
            group_data = GroupUserSchema().dump(group)
            group_data["memberCount"] = member_count
            serialized_items.append(group_data)

        return jsonify({
            'data': serialized_items,
            'meta': meta
        })


@admin_blp.route("/group_user/<int:group_user_id>")
class GroupUser(MethodView):
    """Handles deleting a group user."""
    @role_required([ADMIN_ROLE])
    def delete(self, group_user_id):
        """Deletes a group user and all its related users/data if they exist."""
        group_user = db.session.get(GroupUserModel, group_user_id)
        if not group_user:
            abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)
        
        try:
            for user in group_user.users:
                db.session.delete(user)
            for anonym in group_user.anonyms:
                db.session.delete(anonym)
            for attack in group_user.attacks:
                db.session.delete(attack)

            db.session.delete(group_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Failed to delete group and its users.")
        return jsonify({"message": GROUP_DELETED_SUCCESS}), HTTPStatus.OK
    
@admin_blp.route("/group_user/toggle-ban/<int:group_user_id>")
class ToggleBan(MethodView):
    """Toggles ban status of a group."""
    @role_required([ADMIN_ROLE])
    def put(self, group_user_id):
        """Toggles the ban status of a group."""
        group_user = db.session.get(GroupUserModel, group_user_id)
        if not group_user:
            abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)
        try:
            group_user.is_banned = not group_user.is_banned
            db.session.commit()
            status = "banned" if group_user.is_banned else "unbanned"
            return jsonify({"message": f"Group {group_user.name} has been {status}.",
                            "is_banned": group_user.is_banned}), HTTPStatus.OK
        except Exception:
            db.session.rollback()
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Failed to toggle ban status.")


@admin_blp.route("/group_user/<int:group_user_id>/details")
class GroupUserDetails(MethodView):
    """Handles detailed group information retrieval."""
    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.OK, GroupDetailSchema)
    def get(self, group_user_id):
        """Retrieves detailed information about a group including members, statistics, and recent files."""
        group_detail = get_group_detail(group_user_id)
        if not group_detail:
            abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)
        
        return ResponseBuilder().success(
            message="Group details retrieved successfully",
            data=group_detail
        ).build()


@admin_blp.route("/group_user/<int:group_user_id>/name")
class GroupUserName(MethodView):
    """Handles updating group name."""
    @role_required([ADMIN_ROLE])
    @admin_blp.arguments(UpdateGroupNameSchema)
    def put(self, name_data, group_user_id):
        """Updates the name of a group."""
        new_name = name_data['name']

        # Check if name already exists
        existing_group = db.session.scalar(
            select(GroupUserModel).where(GroupUserModel.name == new_name)
        )
        if existing_group:
            abort(HTTPStatus.CONFLICT, message="Group name already exists.")

        success = update_group_name(group_user_id, new_name)
        if not success:
            abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)
        
        return ResponseBuilder().success(
            message=f"Group name updated to '{new_name}'",
            data=None
        ).build()


@admin_blp.route("/group_user/<int:group_user_id>/members/<int:user_id>")
class GroupUserMember(MethodView):
    """Handles deleting a user from a group."""
    @role_required([ADMIN_ROLE])
    def delete(self, group_user_id, user_id):
        try:
            group_deleted = False

            with db.session.begin():
                user = db.session.get(UserModel, user_id)   

                if not user or user.group_id != group_user_id:
                    abort(HTTPStatus.NOT_FOUND, message="User not found in this group")
                
                db.session.delete(user)

                remaining_users = (
                    db.session.query(UserModel)
                    .filter(UserModel.group_id == group_user_id)
                    .count()
                )

                if remaining_users == 0:
                    db.session.query(AnonymModel).filter(AnonymModel.group_id == group_user_id).delete()
                    db.session.query(AttackModel).filter(AttackModel.group_id == group_user_id).delete()

                    group = db.session.get(GroupUserModel, group_user_id)
                    if group:
                        db.session.delete(group)
                        group_deleted = True

            return ResponseBuilder().success(
                message="User deleted from group successfully",
                data={"group_deleted": group_deleted}
            ).build()

        except SQLAlchemyError as e:
            db.session.rollback()
            return ResponseBuilder().error(
                message="Failed to delete user and clean up group",
                error=str(e),
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            ).build()

