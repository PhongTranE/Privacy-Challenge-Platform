from marshmallow import Schema, fields
from src.constants.app_msg import MISSING_FIELD_ERROR

class InviteKeySchema(Schema):
    key = fields.Str(required=True)
    created = fields.DateTime(required=True)
    is_expired = fields.Bool(required=True)
    creator_id = fields.Int(allow_none=True)
