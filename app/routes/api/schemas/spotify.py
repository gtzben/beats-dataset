"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""

from marshmallow import Schema, fields, post_dump

class SpotifyAccountSchema(Schema):

    """
    TODO
    """
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True)
    participant_id = fields.Integer(dump_only=True)
    email = fields.Email(dump_only=True)
    cache_path = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_dump(pass_many=True)
    def wrap(self, data, many, **karwgs):
        if many:
            return {'data': data}
        return data
