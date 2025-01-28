"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-23
"""

from marshmallow import Schema, fields, post_dump
from flask import current_app

class MusicListeningSchema(Schema):

    """
    TODO
    """
    class Meta:
        ordered = True

    id = fields.Integer(dump_only=True)
    participant_pid = fields.String(dump_only=True)
    account_email = fields.String(dump_only=True)
    listening_session_id = fields.Integer(dump_only=True)
    track_session_id = fields.Integer(dump_only=True)
    track_name = fields.String(dump_only=True)
    track_uri = fields.String(dump_only=True)
    device_type = fields.String(dump_only=True)
    context = fields.Method("get_uri_context")
    playback_inconsistency = fields.Boolean(dump_only=True)
    offline_playback = fields.Boolean(dump_only=True)
    started_at = fields.DateTime(dump_only=True)
    ended_at = fields.DateTime(dump_only=True)

    @post_dump(pass_many=True)
    def wrap(self, data, many, **karwgs):
        if many:
            return {'data': data}
        return data
    
    def get_uri_context(self, obj):
        # Check if the object has a context_uri attribute or is a list of objects
        if isinstance(obj, list) or hasattr(obj, "__iter__"):  # For InstrumentedList or other iterables
            # Retrieve context_uri values from each item in the list and map them
            return [current_app.config["STUDY_PLAYLISTS"].get(item.context_uri, "Other") for item in obj]
        elif hasattr(obj, "context_uri"):  # Handle single object
            return current_app.config["STUDY_PLAYLISTS"].get(obj.context_uri, "Other")
        return "Other"
