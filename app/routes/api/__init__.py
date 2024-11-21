"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from flask import Blueprint
from flask_restful import Api
from app.routes.api.resources import spotify, user, token, participant, device

# Create a blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Attach Flask-RESTful API to the blueprint
api = Api(api_bp)

#### Add resources with their respective endpoints ###

# User related resources
api.add_resource(user.UserResource, '/users', '/users/<int:user_id>')
api.add_resource(user.UserVerifyResource, f'/users/verify/<string:token>')

# Participant related resources
api.add_resource(participant.ParticipantResource, '/participants', '/participants/<string:participant_pid>')
api.add_resource(participant.ParticipantVerifyResource, '/participants/verify/<string:token>')
api.add_resource(participant.ParticipantLinkResources, '/participants/<string:participant_pid>/link_resources')
api.add_resource(participant.ParticipantUnlinkResources, '/participants/<string:participant_pid>/unlink_resources')
api.add_resource(participant.ParticipantActiveResource, '/participants/<string:participant_pid>/status')

# Device related resources
api.add_resource(device.DeviceResource, '/devices', '/devices/<string:device_serial>')

# Spotify related resources
api.add_resource(spotify.SpotifyResource, '/spotify')
# api.add_resource(spotify.SpotifyRedirectResource, '/spotify/callback')


# Session login resources
api.add_resource(token.LoginResource, f'/login')
api.add_resource(token.RefreshResource, f'/refresh')
api.add_resource(token.LogoutResource, f'/logout')