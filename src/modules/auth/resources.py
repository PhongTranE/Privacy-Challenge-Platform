from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import current_app

from src.extensions import db, limiter
from sqlalchemy import select
from src.modules.auth.schemas import (
    UserLoginSchema,
    UserRegisterSchema,
    ChangePasswordSchema,
    ResetPasswordSchema,
    SendEmailSchema,
    GroupUserSchema,
)
from src.modules.auth.models import UserModel, GroupUserModel

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from src.modules.auth.services import (
    validate_password,
    verify_token,
    verify_password,
    create_user,
)
from src.modules.auth.tasks import (
    send_activation_email_task,
    send_password_reset_email_task,
)

from http import HTTPStatus
from src.constants.app_msg import *
from src.common.response_builder import ResponseBuilder
from flask import request

blp = Blueprint("auth_func", __name__, description="Authentication and User Management")


@blp.route("/login")
class UserLogin(MethodView):
    """Handles user login and JWT token generation."""

    @blp.arguments(UserLoginSchema)
    def post(self, user_data):
        """Authenticates a user and returns access and refresh tokens."""
        stm = select(UserModel).where(UserModel.username == user_data["username"])
        user = db.session.execute(stm).scalars().first()

        current_app.logger.info(f"Login attempt for username: {user_data['username']}")

        if not user:
            current_app.logger.warning(f"User '{user_data['username']}' not found.")
            abort(HTTPStatus.UNAUTHORIZED, message=INVALID_CREDENTIALS)

        if not user.is_active:
            abort(HTTPStatus.UNAUTHORIZED, message=ACCOUNT_NOT_ACTIVATED)

        if verify_password(user_data["password"], user._password):
            if not isinstance(user.id, int):
                abort(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=INVALID_FORMAT.format("user_id", "number"),
                )

            user_id = str(user.id)
            current_app.logger.info(f"Login successful for user: {user.username}")

            access_token = create_access_token(
                identity=user_id,
                fresh=True,
                additional_claims={
                    "roles": [role.name for role in user.roles],
                    "group": user.group.id if user.group else None,
                },
            )
            refresh_token = create_refresh_token(identity=user_id)

            user_data = UserLoginSchema().dump(user)
            data = {"access_token": access_token, "user": user_data}
            res = (
                ResponseBuilder()
                .success(
                    message=LOGIN_SUCCESS, data=data, status_code=HTTPStatus.CREATED
                )
                .build()
            )
            set_refresh_cookies(res, refresh_token)
            return res

        current_app.logger.warning(
            f"Login failed for username: {user_data['username']}"
        )
        abort(HTTPStatus.UNAUTHORIZED, message=INVALID_CREDENTIALS)


@blp.route("/refresh")
class TokenRefresh(MethodView):
    """Handles token refresh to issue a new access token."""

    @jwt_required(locations=["cookies"], refresh=True)
    def post(self):
        """Issues a new access token using a valid refresh token."""
        current_user_id = get_jwt_identity()
        user = db.session.get(UserModel, current_user_id)

        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)

        roles = [role.name for role in user.roles]

        new_token = create_access_token(
            identity=current_user_id,
            fresh=False,
            additional_claims={
                "roles": roles,
                "group": user.group.id if user.group else None,
            },
        )
        return (
            ResponseBuilder()
            .success(
                message=REFRESH_SUCCESS,
                data={"access_token": new_token},
                status_code=HTTPStatus.CREATED,
            )
            .build()
        )


@blp.route("/register")
class UserRegister(MethodView):
    """Handles new user registration."""

    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        """Registers a new user."""
        current_app.logger.info(f"User registration attempt: {user_data['username']}")
        try:
            user = create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                invite_key=user_data["invite_key"],
                group_name=user_data["group_name"],
                is_active=False,
            )
            current_app.logger.info(f"User created successfully: {user.username}")
            return (
                ResponseBuilder()
                .success(
                    message=REGISTER_SUCCESS,
                    data={"user": UserRegisterSchema().dump(user)},
                    status_code=HTTPStatus.CREATED,
                )
                .build()
            )

        except ValueError as e:
            abort(HTTPStatus.BAD_REQUEST, message=str(e))
        except RuntimeError as e:
            current_app.logger.error(f"Database error during registration: {str(e)}")
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message=INTERNAL_SERVER_ERROR)


@blp.route("/activation/<string:token>")
class UserActivateAccount(MethodView):
    """""Activates a user account using an activation token.""" ""

    def get(self, token):
        """Activates a user's account if the token is valid."""
        email = verify_token(token)
        if email:
            stm = select(UserModel).where(UserModel.email == email)
            user = db.session.execute(stm).scalars().first()
            if user:
                user.is_active = True
                db.session.commit()
                current_app.logger.info(USER_ACTIVATED.format(email))
                return (
                    ResponseBuilder()
                    .success(
                        message=USER_ACTIVATED.format(email), status_code=HTTPStatus.OK
                    )
                    .build()
                )
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)
        abort(HTTPStatus.BAD_REQUEST, message=INVALID_OR_EXPIRED_TOKEN)


@limiter.limit("1 per 2 minutes")
@blp.route("/resend_activation")
class UserResendActivateAccount(MethodView):
    """Handles resending the account activation email."""

    @blp.arguments(SendEmailSchema)
    def post(self, user_data):
        """Resends an activation email to a user if their account is not yet activated."""
        stm = select(UserModel).where(UserModel.email == user_data["email"])
        user = db.session.execute(stm).scalars().first()

        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)
        if user.is_active:
            abort(HTTPStatus.CONFLICT, message=USER_ALREADY_ACTIVATED)

        try:
            send_activation_email_task.delay(user.email)
            current_app.logger.info(f"Activation email resent to: {user.email}")

        except Exception as e:
            current_app.logger.error(f"Error resending activation email: {str(e)}")
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message=INTERNAL_SERVER_ERROR)

        return (
            ResponseBuilder()
            .success(message=ACTIVATION_EMAIL_RESENT, status_code=HTTPStatus.OK)
            .build()
        )


@blp.route("/change_password")
class ChangePassword(MethodView):
    """Allows an authenticated user to change their password."""

    @jwt_required(fresh=True)
    @blp.arguments(ChangePasswordSchema)
    def post(self, user_data):
        """Change the user's password."""
        user_id = get_jwt_identity()  # Get user ID from JWT token
        current_app.logger.info(f"Password change attempt")

        old_password = user_data["old_password"]
        new_password = user_data["new_password"]

        try:
            validate_password(new_password)
        except ValueError as e:
            abort(HTTPStatus.BAD_REQUEST, message=str(e))

        user = db.session.get(UserModel, user_id)

        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)

        if not verify_password(old_password, user._password):
            abort(HTTPStatus.UNAUTHORIZED, message=INCORRECT_OLD_PASSWORD)

        user.password = new_password
        db.session.commit()

        current_app.logger.info(f"User {user.username} changed their password.")

        return (
            ResponseBuilder()
            .success(message=PASSWORD_CHANGED_SUCCESS, status_code=HTTPStatus.OK)
            .build()
        )


@blp.route("/forgot_password")
class ForgotPassword(MethodView):
    """Allows users to request a password reset token."""

    @blp.arguments(SendEmailSchema)
    def post(self, user_data):
        """Sends a password reset email."""
        stm = select(UserModel).where(UserModel.email == user_data["email"])
        user = db.session.execute(stm).scalars().first()

        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)

        # Send the reset email
        try:
            send_password_reset_email_task.delay(user.email)
        except RuntimeError as e:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message=INTERNAL_SERVER_ERROR)

        return (
            ResponseBuilder()
            .success(message=PASSWORD_RESET_EMAIL_SENT, status_code=HTTPStatus.OK)
            .build()
        )


@blp.route("/reset-password/<string:reset_token>")
class ResetPassword(MethodView):
    """Allows users to reset their password using a token."""

    @blp.arguments(ResetPasswordSchema)
    def post(self, user_data, reset_token):
        """Reset the user's password using a valid token."""
        new_password = user_data["new_password"]

        email = verify_token(reset_token)
        if not email:
            abort(HTTPStatus.BAD_REQUEST, message=INVALID_OR_EXPIRED_TOKEN)

        stm = select(UserModel).where(UserModel.email == email)
        user = db.session.execute(stm).scalars().first()
        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)

        try:
            validate_password(new_password)
        except ValueError as e:
            abort(HTTPStatus.BAD_REQUEST, message=str(e))

        user.password = new_password
        db.session.commit()

        return (
            ResponseBuilder()
            .success(message=PASSWORD_RESET_SUCCESS, status_code=HTTPStatus.OK)
            .build()
        )


@blp.route("/logout")
class Logout(MethodView):
    """Logs out a user by revoking their token."""

    @jwt_required(locations=["cookies"], refresh=True)
    def post(self):
        res = (
            ResponseBuilder()
            .success(message=LOGOUT_SUCCESS, status_code=HTTPStatus.OK)
            .build()
        )
        unset_jwt_cookies(res)
        return res


@blp.route("/me")
class MyInfo(MethodView):
    """Retrieve my info"""

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = db.session.get(UserModel, user_id)

        if not user:
            abort(HTTPStatus.NOT_FOUND, message=USER_NOT_FOUND)

        user_data = UserLoginSchema().dump(user)

        return (
            ResponseBuilder()
            .success(
                message=ME_SUCCESS, data={"user": user_data}, status_code=HTTPStatus.OK
            )
            .build()
        )


@blp.route("/check-group", methods=["GET"])
def check_group():
    group_name = request.args.get("name")

    if not group_name:
        abort(HTTPStatus.BAD_REQUEST, message="Missing 'name' query parameter.")

    stm = select(GroupUserModel).where(GroupUserModel.name == group_name)
    group = db.session.execute(stm).scalars().first()

    if not group:
        abort(HTTPStatus.NOT_FOUND, message=GROUP_NOT_FOUND)

    return (
        ResponseBuilder()
        .success(
            message=GROUP_FOUND, data={"group": group_name}, status_code=HTTPStatus.OK
        )
        .build()
    )
