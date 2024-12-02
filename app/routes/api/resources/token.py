"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from http import HTTPStatus
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import (create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt
)

from app.utils import check_password
from app.routes.api.models.user import User

# revoked tokens are stored in memory at the moment
# in case the app reboots, revoked valid tokens
# can have access to protected endpoints
black_list = set()

class LoginResource(Resource):

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    def post(self):

        json_data = request.get_json()

        email = json_data.get('email')
        password = json_data.get('password')

        user = User.get_by_email(email=email)

        if not user or not check_password(password,user.password):
            return {'message':'Email or password is incorrect'}, HTTPStatus.UNAUTHORIZED

        if user.is_verified is False:
            return {'message': 'The user account is not verified yet'}, HTTPStatus.FORBIDDEN
        
        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(identity=user.id)

        self.logger.debug(f"User {user.email} has logged in!")

        return {'access_token':access_token,'refresh_token':refresh_token},HTTPStatus.OK


class RefreshResource(Resource):

    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()

        token = create_access_token(identity=current_user,fresh=False)

        return {'access_token': token}, HTTPStatus.OK


class LogoutResource(Resource):

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']

        black_list.add(jti)

        current_user = User.get_by_id(id=get_jwt_identity())

        self.logger.debug(f"User {current_user.email} has logged out!")

        return {'message': 'Successfully logged out'}, HTTPStatus.OK