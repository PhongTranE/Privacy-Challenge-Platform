from marshmallow import Schema, fields, validate, ValidationError, validates_schema

from src.modules.auth.services import validate_password_match
from src.constants.app_msg import *
from password_validator import PasswordValidator


password_schema = (
    PasswordValidator()
    .min(8)
    .max(128)
    .has()
    .uppercase()
    .has()
    .lowercase()
    .has()
    .digits()
    .has()
    .symbols()
)


# Define the validation function
def validate_password(password):
    if not password_schema.validate(password):
        raise ValidationError(
            "Password must be 8-128 characters long, contain uppercase, lowercase, a digit and a symbol."
        )


email_validator = validate.And(
    validate.Email(error=INVALID_FORMAT.format("email", "email")),
    validate.Length(max=255, error="Email must be at most 255 characters long."),
)


class BaseRoleSchema(Schema):
    name = fields.Str(dump_only=True)


class RoleSchema(BaseRoleSchema):
    id = fields.Int(dump_only=True)
    default = fields.Bool(dump_only=True)


class UserRegisterSchema(Schema):
    id = fields.Int(
        dump_only=True,
        error_messages={"invalid": INVALID_FORMAT.format("id", "number")},
    )

    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={
            "required": MISSING_FIELD_ERROR.format("username"),
            "null": NON_NULL_ERROR.format("username"),
            "validator_failed": "Username must be between 3 and 50 characters.",
        },
    )

    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate_password,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("password"),
            "null": NON_NULL_ERROR.format("password"),
        },
    )

    roles = fields.List(
        fields.Nested(BaseRoleSchema()),
        dump_only=True,
        error_messages={"invalid": "Roles must be a list of valid role objects."},
    )

    is_active = fields.Bool(
        dump_only=True,
        error_messages={"invalid": "Active status must be a boolean (true or false)."},
    )
    email = fields.Str(
        required=True,
        validate=email_validator,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("email"),
            "null": NON_NULL_ERROR.format("email"),
        },
    )

    confirm_password = fields.Str(
        load_only=True,
        required=True,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("confirm_password"),
        },
    )

    invite_key = fields.Str(
        required=True,
        load_only=True,
        error_messages={"required": MISSING_FIELD_ERROR.format("invite_key")},
    )

    group_name = fields.Str(
        required=True,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("group_name"),
        },
    )

    @validates_schema
    def check_passwords(self, data, **kwargs):
        validate_password_match(data)


class GroupUserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        error_messages={"required": MISSING_FIELD_ERROR.format("group_name")},
    )
    is_banned = fields.Bool(dump_only=True)
    member_count = fields.Int(dump_only=True)

class UserLoginSchema(Schema):
    id = fields.Int(
        dump_only=True,
    )

    username = fields.Str(
        required=True,
    )

    password = fields.Str(
        required=True,
        load_only=True,
    )

    roles = fields.List(fields.Nested(BaseRoleSchema()), dump_only=True)

    is_active = fields.Bool(
        dump_only=True,
    )
    email = fields.Str(dump_only=True)
    group = fields.Nested(GroupUserSchema(), dump_only=True)


class ChangePasswordSchema(Schema):
    old_password = fields.Str(
        load_only=True,
        required=True,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("old_password"),
            "null": NON_NULL_ERROR.format("old_password"),
        },
    )
    new_password = fields.Str(
        load_only=True,
        required=True,
        validate=validate_password,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("new_password"),
            "null": NON_NULL_ERROR.format("new_password"),
        },
    )
    confirm_password = fields.Str(
        load_only=True,
        required=True,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("confirm_password"),
        },
    )

    @validates_schema
    def check_passwords(self, data, **kwargs):
        validate_password_match(data, password_field="new_password", confirm_field="confirm_password")


class ResetPasswordSchema(Schema):
    new_password = fields.Str(
        load_only=True,
        required=True,
        validate=validate_password,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("new_password"),
        },
    )


class SendEmailSchema(Schema):
    email = fields.Str(
        required=True,
        validate=email_validator,
        error_messages={
            "required": MISSING_FIELD_ERROR.format("email"),
            "null": NON_NULL_ERROR.format("email"),
        },
    )


