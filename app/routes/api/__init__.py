"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from flask import Blueprint
from flask_restful import Api
from app.routes.api.resources import user, token

# Create a blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Attach Flask-RESTful API to the blueprint
api = Api(api_bp)

#### Add resources with their respective endpoints ###

# User related resources
api.add_resource(user.UserResource, '/users', '/users/<int:user_id>')
api.add_resource(user.UserActivateResource, f'/users/activate/<string:token>')

# Session login resources
api.add_resource(token.LoginResource, f'/login')
api.add_resource(token.RefreshResource, f'/refresh')
api.add_resource(token.LogoutResource, f'/logout')