"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""

from marshmallow import Schema, fields, validates, post_dump,  ValidationError
from app.routes.api.schemas.user import UserSchema
from app.routes.api.schemas.device import DeviceSchema
from app.routes.api.schemas.spotify import SpotifyAccountSchema
from app.routes.api.schemas.music import MusicListeningSchema



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
    device = fields.Nested(DeviceSchema, attribute='device', dump_only=True, only=['device_name','serial_number', "measurement_location"])
    spotify = fields.Nested(SpotifyAccountSchema, attribute='spotifyaccount', dump_only=True, only=['account_email','cache_path'])
    music_listening = fields.Nested(MusicListeningSchema, attribute='musiclistening', many=True, dump_only=True, only=['id','track_uri', 'context', 'started_at', 'ended_at'])


    @post_dump(pass_many=True)
    def wrap(self, data, many, **karwgs):
        if many:
            return {'data': data}
        return data


    @validates('ndh')
    def validate_ndh(self, value):
        # Normalize value to lowercase for comparison
        normalized_value = value.strip().lower()
        
        # Check if the input matches either "left" or "right"
        if normalized_value not in ['left', 'right']:
            raise ValidationError("Non-dominant hand must be 'left' or 'right'.")

class ParticipantFlatSchema(Schema):
    """
    TODO
    """
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True)
    pid = fields.String(dump_only=True)
    device_serial = fields.String(dump_only=True)
    spotify_account = fields.String(dump_only=True)
    ndh = fields.String(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    is_verified = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_dump(pass_many=True)
    def wrap(self, data, many, **karwgs):
        if many:
            return {'data': data}
        return data