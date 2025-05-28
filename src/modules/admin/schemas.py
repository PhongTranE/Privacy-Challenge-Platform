from marshmallow import Schema, fields, validate
from src.constants.app_msg import MISSING_FIELD_ERROR

class InviteKeySchema(Schema):
    key = fields.Str(dump_only=True)
    created = fields.DateTime(dump_only=True)
    is_expired = fields.Bool(required=True)
    creator_id = fields.Int(allow_none=True)

# Add new schema for group management
class GroupMemberSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    email = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)

class GroupFileSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    file_type = fields.Str(dump_only=True)  # 'anonymous' or 'attack'
    created_at = fields.DateTime(dump_only=True)
    score = fields.Float(dump_only=True)
    is_published = fields.Bool(dump_only=True)
    file_path = fields.Str(dump_only=True)

class GroupStatisticsSchema(Schema):
    total_anonymous_files = fields.Int(dump_only=True)
    published_anonymous_files = fields.Int(dump_only=True)
    total_attack_files = fields.Int(dump_only=True)
    defense_score = fields.Float(dump_only=True)
    attack_score = fields.Float(dump_only=True)
    total_score = fields.Float(dump_only=True)

class GroupBaseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    is_banned = fields.Bool(dump_only=True)
    member_count = fields.Int(dump_only=True)

class GroupDetailSchema(Schema):
    group = fields.Nested(GroupBaseSchema, dump_only=True)
    members = fields.List(fields.Nested(GroupMemberSchema), dump_only=True)
    statistics = fields.Nested(GroupStatisticsSchema, dump_only=True)
    recent_files = fields.List(fields.Nested(GroupFileSchema), dump_only=True)

class UpdateGroupNameSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=64))
