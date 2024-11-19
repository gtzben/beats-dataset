"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

import os

from flask import request, url_for, current_app, render_template, make_response
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from http import HTTPStatus

from marshmallow import ValidationError

from app.routes.api.models.user import User

from app.utils import generate_token, verify_token, send_email

from app.routes.api.schemas.user import UserSchema



user_schema = UserSchema()
users_schema = UserSchema(many=True)


class UserResource(Resource):
    """
    TODO

    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger  # Access the app logger


    @jwt_required()
    def get(self, user_id=None):

        """
        TODO

        """
        #
        current_user = User.get_by_id(id=get_jwt_identity())

        #
        if current_user.is_superuser or current_user.is_admin:
            if user_id:
                user = User.get_by_id(id=user_id, show_deleted=True)

                if user is None:
                    return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
                
                data = user_schema.dump(user)
            else:
                all_users = User.get_all_users()
                data = users_schema.dump(all_users)
            return data, HTTPStatus.OK
        else:
            return {"message":"You are not allowed to see this information"}, HTTPStatus.FORBIDDEN


    def post(self):

        """
        TODO

        DONE
        - Add super user role
        - Add admin role

        """

        json_data = request.get_json()

        try:
            data = user_schema.load(json_data)
        except ValidationError as errors:
            return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST
        
        if User.get_by_email(data.get('email')):
            return {'message': 'email already used'}, HTTPStatus.BAD_REQUEST

        user = User(**data)

        if not User.get_all_users():
            user.is_superuser = True

        user.save()

        token = generate_token(user.email, salt='activate')

        subject = 'Please, confirm your registration.'

        link = url_for('api.useractivateresource',
                       token=token,
                       _external=True)


        send_email(to=user.email,
                   subject=subject,
                   link=link,
                   html='email_verification.html')

        user_created = user_schema.dump(user)

        self.logger.debug(f"Account for {user.email} has been created!")

        return user_created, HTTPStatus.CREATED



class UserActivateResource(Resource):
    """
    TODO
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger


    def get(self, token):

        """
        TODO
        
        """

        email = verify_token(token, max_age=(60 * 60 * 24),salt='activate') # Token expires in 1 day

        if email is False:
            return {'message': 'Invalid token or token expired'}, HTTPStatus.BAD_REQUEST

        user = User.get_by_email(email=email)

        if not user:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        if user.is_verified is True:
            return {'message': 'The user account is already activated'}, HTTPStatus.BAD_REQUEST

        user.is_verified = True
        user.save()

        self.logger.debug(f"User account of {user.email} has been activated!")

        # return {"message":"Your account has been activated!"}, HTTPStatus.OK
        return make_response(render_template('account_activated.html'), HTTPStatus.OK, {'Content-Type': 'text/html'})


# class SingleUserResource(Resource):

#     """
#     TODO
    
#     """

#     def __init__(self, **kwargs):
#         self.logger = kwargs.get('logger')

#     @jwt_required()
#     def get(self, id):

#         """
#         TODO
        
#         """

#         current_user = User.get_by_id(id=get_jwt_identity())

#         if current_user.is_superuser:
#             user = User.get_by_id(id=id, show_deleted=True)

#             if user is None:
#                 return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
            
#             data = user_schema.dump(user)
#             return data, HTTPStatus.OK
        
#         else:
#             return {"message":"You are not allowed to see this information"}, HTTPStatus.FORBIDDEN
        
#     @jwt_required()
#     def delete(self, id):
#         """
#         TODO

#         - Soft delete users
#         """

#         current_user = User.get_by_id(id=get_jwt_identity())

#         if current_user.is_superuser:
#             user = User.get_by_id(id=id, show_deleted=True)

#             if user is None:
#                 return {"message": "User not found."}, HTTPStatus.NOT_FOUND
            
#             if user.deleted:
#                 return {"message": f"The user {user.id} is already deleted"}, HTTPStatus.CONFLICT
            
#             if current_user.is_superuser and user.is_superuser:
#                 return {"message": f"The super user account cannot be deleted at the moment."}, HTTPStatus.FORBIDDEN
            
#             return {"message":f"User {user.username} has been deleted!"}, HTTPStatus.OK

#         else:
#             return {"message":"You are not allowed to delete this resource"}, HTTPStatus.FORBIDDEN

        
        




