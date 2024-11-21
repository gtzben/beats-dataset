"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from http import HTTPStatus

from flask import request, url_for, current_app, render_template, make_response
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required

from marshmallow import ValidationError

from app.routes.api.schemas.user import UserSchema

from app.routes.api.models.user import User

from app.utils import generate_token, verify_token, send_email


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
                
                data = UserSchema().dump(user)
            else:
                all_users = User.get_all_users()
                data = UserSchema(many=True).dump(all_users)
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
            data = UserSchema().load(json_data)
        except ValidationError as errors:
            return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST
        
        if User.get_by_email(data.get('email')):
            return {'message': 'email already used'}, HTTPStatus.BAD_REQUEST

        user = User(**data)

        if not User.get_all_users():
            user.is_superuser = True

        user.save()

        token = generate_token(user.email, salt='verify')

        #
        subject = 'BEATS Study - Please, confirm your registration to start using the BEATS API'
        title = "Verify Your Email"
        greetings = 'Dear Collaborator,'
        thank_you = 'Welcome, and thank you for contributing to the BEATS dataset.'
        next_steps = 'To complete your registration and access the platform, please confirm your email by clicking the button below:'
        button = "Confirm Your Email"

        link = url_for('api.userverifyresource',
                       token=token,
                       _external=True)

        #
        send_email(user.email,
                   subject,
                   'email_template.html',
                   title=title,
                   greetings=greetings,
                   thank_you=thank_you,
                   next_steps=next_steps,
                   button = "Confirm Your Email",
                   link=link)

        user_created = UserSchema().dump(user)

        self.logger.debug(f"Account for {user.email} has been created! Pending for email verification.")

        return user_created, HTTPStatus.CREATED



class UserVerifyResource(Resource):
    """
    TODO
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger


    def get(self, token):

        """
        TODO
        
        """

        email = verify_token(token, max_age=(60 * 60 * 24),salt='verify') # Token expires in 1 day

        if email is False:
            return {'message': 'Invalid token or token expired'}, HTTPStatus.BAD_REQUEST

        user = User.get_by_email(email=email)

        if not user:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        if user.is_verified is True:
            return {'message': 'The user account is already verified'}, HTTPStatus.BAD_REQUEST

        user.is_verified = True
        user.save()

        self.logger.debug(f"User account of {user.email} has been verified!")

        return make_response(render_template('account_verified.html'), HTTPStatus.OK, {'Content-Type': 'text/html'})