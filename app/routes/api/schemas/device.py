"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""

from marshmallow import Schema, fields, post_dump
import re

class DeviceSchema(Schema):

    """
    TODO
    """
    class Meta:
        ordered = True

    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    participant_id = fields.Integer(dump_only=True)
    device_name = fields.String(required=True)
    serial_number = fields.String(required=True)
    measurement_location = fields.String(required=True)
    is_assigned = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


    @post_dump(pass_many=True)
    def wrap(self, data, many, **karwgs):
        if many:
            return {'data': data}
        return data