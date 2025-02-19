from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class PlainRoleSchema(Schema):
    name = fields.Str(dump_only=True)
class RoleSchema(PlainRoleSchema):
    id = fields.Int(dump_only=True)
    default = fields.Bool(dump_only=True)

class UserSchema(Schema):
    id = fields.Int(
        dump_only=True,
        error_messages={"invalid": "ID must be an integer."}
    )
    
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={
            "required": "Username is required.",
            "null": "Username cannot be null.",
            "validator_failed": "Username must be between 3 and 50 characters."
        }
    )

    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128),
        error_messages={
            "required": "Password is required.",
            "null": "Password cannot be null.",
            "validator_failed": "Password must be between 8 and 128 characters."
        }
    )

    roles = fields.List(
        fields.Nested(PlainRoleSchema()),
        dump_only=True,
        error_messages={"invalid": "Roles must be a list of valid role objects."}
    )

    is_active = fields.Bool(
        dump_only=True,
        error_messages={"invalid": "Active status must be a boolean (true or false)."}
    )

class UserRegisterSchema(UserSchema):
    email = fields.Str(
        required=True,
        validate=[
            validate.Email(error="Invalid email format. Please enter a valid email address."),
            validate.Length(max=255, error="Email must be at most 255 characters long.")
        ],
        error_messages={
            "required": "Email is required.",
            "null": "Email cannot be null."
        }
    )

    invite_key = fields.Str(
        required=True,
        load_only=True,
        error_messages={
            "required": "Invite key is required.",
        }
    )

class ChangePasswordSchema(Schema):
    old_password = fields.Str(
        load_only=True, 
        required=True,
        error_messages={
            "required": "Old password is required.",
            "null": "Old password cannot be null.",
        }
        )
    new_password = fields.Str(
        load_only=True, 
        required=True,
        error_messages={
            "required": "Old password is required.",
            "null": "Old password cannot be null.",
        }
        )

class ResetPasswordSchema(Schema):
    new_password = fields.Str(
        required=True,
        error_messages={
            "required": "New password is required.",
        }
    )
    confirm_password = fields.Str(
        required=True,
        error_messages={"required": "Password confirmation is required."}
    )

    @validates_schema
    def validate_password_match(self, data, **kwargs):
        """Ensures new_password and confirm_password match."""
        if data.get("new_password") != data.get("confirm_password"):
            raise ValidationError({"confirm_password": "Passwords do not match."})

class SendEmailSchema(Schema):
    email = fields.Str(
        required=True,
        validate=[
            validate.Email(error="Invalid email format. Please enter a valid email address."),
            validate.Length(max=255, error="Email must be at most 255 characters long.")
        ],
        error_messages={
            "required": "Email is required.",
            "null": "Email cannot be null."
        }
    )