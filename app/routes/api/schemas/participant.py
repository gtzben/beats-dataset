"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""

from marshmallow import Schema, fields, validates, post_dump,  ValidationError
from app.routes.api.schemas.user import UserSchema

class ParticipantSchema(Schema):

    """
    TODO
    """
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True)
    pid = fields.String(required=True)
    email = fields.Email(required=True)
    ndh = fields.String(required=True)
    is_active = fields.Boolean(dump_only=True)
    is_verified = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    user = fields.Nested(UserSchema, attribute='user', dump_only=True, only=['email','institution'])

    @post_dump(pass_many=True)
    def wrap(self, data, many, **karwgs):
        if many:
            return {'data': data}
        return data


    @validates('ndh')
    def validate_ndh(self,value):
        if len(value)>1:
            raise ValidationError("Non-dominant hand must be a one charachter value, L or R.")
        if value not in ['L', 'R']:
            raise ValidationError("Non-dominant hand must be L for Left or R for Right.")