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
        """

        json_data = request.get_json()

        try:
            data = UserSchema().load(json_data)
        except ValidationError as errors:
            return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST
        
        if User.get_by_email(data.get('email')):
            return {'message': 'Email already used'}, HTTPStatus.BAD_REQUEST

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
                   button = button,
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

        self.logger.info(f"User account of {user.email} has been verified!")

        return make_response(render_template('confirm_token.html', title="Account Verified", confirm='Your account has been successfully verified.'), HTTPStatus.OK, {'Content-Type': 'text/html'})
    

class ResetPwdRequest(Resource):
    """
    TODO

    """

    def post(self):
        """
        TODO
        """
        json_data = request.get_json()

        try:
            data = UserSchema(only=('email',)).load(json_data)
        except ValidationError as errors:
            return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST

        user = User.get_by_email(data.get('email'))

        if not user:
            return {'message': 'There is no account linked to this email'}, HTTPStatus.NOT_FOUND
        
        token = generate_token(user.email, salt='reset')
   
        #
        subject = 'BEATS Study - Reset password request'
        title = "Reset Your Password"
        greetings = 'Dear Collaborator,'
        thank_you = ''
        next_steps = 'To reset your password click on the link below. If you have not requested a password reset simply ignore this message.'
        button = "Reset Your Password"

        link = url_for('portal.reset_password',
                       reset_pwd_token=token,
                       _external=True)

        #
        send_email(user.email,
                   subject,
                   'email_template.html',
                   title=title,
                   greetings=greetings,
                   thank_you=thank_you,
                   next_steps=next_steps,
                   button = button,
                   link=link)

        return {"message": "An email has been sent with instructions to reset your password."}, HTTPStatus.OK
    


class ResetPwd(Resource):
    """
    TODO

    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger


    def post(self):
        """

        """

        #
        json_data = request.get_json()

        #
        try:
            reset_pwd_token = json_data.pop("reset_pwd_token")
            email = verify_token(reset_pwd_token, salt='reset')
            if email is False:
                raise ValueError("Invalid token or token expired")
        except (KeyError, ValueError) as error:
            return {'message': f'Token not sent or there is an issue with the token: {error}'}, HTTPStatus.BAD_REQUEST
        
        try:
            hashed_password = UserSchema(only=('password',)).load(json_data)
        except ValidationError as errors:
            return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST
        
        user = User.get_by_email(email=email)

        if not user:
            return {'message': 'There is no account linked to this email'}, HTTPStatus.NOT_FOUND

        if user.is_verified is False:
            return {'message': 'The user account has not been activated yet.'}, HTTPStatus.BAD_REQUEST
        
        #
        user.password = hashed_password['password']
        user.save()
        self.logger.debug(f"User {user.email} has reset his/her password!")

        return {"message":"Your password has been updated. You are now able to login."}, HTTPStatus.OK
        
            

