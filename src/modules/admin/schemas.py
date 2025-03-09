from marshmallow import Schema, fields

class InviteKeySchema(Schema):
    key = fields.Str(dump_only=True)
    created = fields.DateTime(dump_only=True)
