"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from marshmallow import Schema, fields, post_dump
from app.utils import hash_password


class UserSchema(Schema):

    """
    TODO
    """
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    password = fields.Method(required=True, deserialize='load_password')
    institution = fields.String(required=True)
    is_verified = fields.Boolean(dump_only=True)
    is_superuser = fields.Boolean(dump_only=True)
    is_admin = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_dump(pass_many=True)
    def wrap(self, data, many, **karwgs):
        if many:
            return {'data': data}
        return data

    def load_password(self, pw):
        return hash_password(pw)