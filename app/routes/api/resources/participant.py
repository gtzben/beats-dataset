"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""

from http import HTTPStatus

from flask import current_app, request, make_response, render_template, url_for
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required

from marshmallow import ValidationError
from app.routes.api.schemas.participant import ParticipantSchema
from app.routes.api.schemas.link import LinkSchema

from app.routes.api.models.user import User
from app.routes.api.models.participant import Participant

from app.utils import generate_token, verify_token, send_email, encrypt_email, hash_email


class ParticipantResource(Resource):

    """
    TODO
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger


    @jwt_required()
    def get(self, participant_pid=None):

        """
        TODO

        """
        current_user = User.get_by_id(id=get_jwt_identity())

        if current_user.is_superuser or current_user.is_admin:
            if participant_pid:
                participant = Participant.get_by_pid(pid=participant_pid)

                if participant is None:
                    return {'message': 'Participant not found'}, HTTPStatus.NOT_FOUND
                
                data = ParticipantSchema().dump(participant)

            else:
                all_participants = Participant.get_all_participants()
                data = ParticipantSchema(many=True).dump(all_participants)

            return data
        else:
            return {"message":"You are not allowed to see this information"}, HTTPStatus.FORBIDDEN
            


    @jwt_required()
    def post(self):
        """

        """

        json_data = request.get_json()

        current_user = User.get_by_id(id=get_jwt_identity())

        if current_user.is_superuser or current_user.is_admin:

            try:
                data = ParticipantSchema().load(json_data)
            except ValidationError as errors:
                return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST

            if Participant.get_by_pid(data.get('pid')):
                return {'message': 'This participant has already been registered in the study'}, HTTPStatus.BAD_REQUEST

            #
            participant_email = data.get("email")
            email_hash = hash_email(participant_email)
            email_encrypted = encrypt_email(participant_email)
            data.pop("email", None)

            #
            participant = Participant(**data)
            participant.user_id = current_user.id
            participant.email_hash = email_hash
            participant.email_encrypted = email_encrypted
            participant.save()

            token = generate_token(participant_email, salt='verify')

            subject = 'BEATS Study - Please, confirm your registration to participte in this study.'
            title = "Verify Your Account"
            greetings = 'Dear Participant,'
            thank_you = 'Thank you for joining this data collection study. Your participation is crucial for advancing our research in music and its impact on well-being.'
            next_steps = 'To complete your registration and begin the data collection process, please confirm your email by clicking the button below:'
            button = "Confirm Your Email"
            link = url_for('api.participantverifyresource',
                        token=token,
                        _external=True)

            #
            send_email(participant_email,
                       subject,
                       'email_template.html',
                       participant.pid,
                       title=title,
                       greetings=greetings,
                       thank_you=thank_you,
                       next_steps=next_steps,
                       button=button,
                       link=link)

            participant_created = ParticipantSchema().dump(participant)

            self.logger.debug(f"User {current_user.email} has registered participant {participant.pid}! Pending for email validation.")

            return participant_created, HTTPStatus.CREATED
        
        else:
            return {"message":"You are not allowed to sign up participants"}, HTTPStatus.FORBIDDEN
        

class ParticipantVerifyResource(Resource):
    """
    TODO
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger


    def get(self, token):

        """
        TODO
        
        """
        
        #
        email = verify_token(token, max_age=(60 * 60 * 24),salt='verify') # Token expires in 1 day

        if email is False:
            return {'message': 'Invalid token or token expired'}, HTTPStatus.BAD_REQUEST

        #
        email_hash = hash_email(email)
        participant = Participant.get_by_email_hash(email_hash=email_hash)

        if not participant:
            return {'message': 'Participant not found'}, HTTPStatus.NOT_FOUND

        if participant.is_verified is True:
            return {'message': 'The participant profile is already verified'}, HTTPStatus.BAD_REQUEST

        participant.is_verified = True
        participant.save()

        self.logger.debug(f"Participant {participant.pid} has been verified!")

        return make_response(render_template('account_verified.html'), HTTPStatus.OK, {'Content-Type': 'text/html'})
    

class ParticipantLinkResources(Resource):

    """
    TODO
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def patch(self, participant_pid):
        
        json_data = request.get_json()
        
        current_user = User.get_by_id(id=get_jwt_identity())
        
        if current_user.is_superuser or current_user.is_admin:

            try:
                data = LinkSchema().load(json_data)
            except ValidationError as errors:
                return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST
            
            participant = Participant.get_by_pid(pid=participant_pid)
            if participant is None:
                return {'message': f'Participant {participant_pid} not found in DB'}, HTTPStatus.NOT_FOUND
            
            if not participant.is_verified:
                return {'message': "Verification of the participant's e-mail address is still pending."}, HTTPStatus.BAD_REQUEST

            if data.get('serial_number'):
                if Participant.get_by_linked_device(serial_number=data.get('serial_number')):
                    return {'message': f"The device {data.get('serial_number')} has already being assigned"}, HTTPStatus.BAD_REQUEST
                participant.device_serial = data.get('serial_number')
                participant.save()

            if data.get('account_email'):
                if Participant.get_by_linked_spotify(account_email=data.get('account_email')):
                    return {'message': f"The account {data.get('account_email')} has already being assigned"}, HTTPStatus.BAD_REQUEST
                participant.spotify_account = data.get('account_email')
                participant.save()

            self.logger.info(f"Device {participant.device_serial} and account {participant.spotify_account} are linked to participant {participant_pid}.")

            return {"message": "Device association to participant was successful"}, HTTPStatus.OK    

        else:
            return {"message":"You are not allowed to associate resources to participants"}, HTTPStatus.FORBIDDEN


class ParticipantUnlinkResources(Resource):

    """
    TODO
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def patch(self, participant_pid):
        
        
        current_user = User.get_by_id(id=get_jwt_identity())
        
        if current_user.is_superuser or current_user.is_admin:

            participant = Participant.get_by_pid(pid=participant_pid)
            if participant is None:
                return {'message': f"Participant {participant_pid} not found in DB"}, HTTPStatus.NOT_FOUND
            
            if not participant.is_verified:
                return {'message': "Verification of the participant's e-mail address is still pending."}, HTTPStatus.BAD_REQUEST

            if participant.is_active:
                return {'message': "Unable to unlink resoruces since participant is still active."}, HTTPStatus.BAD_REQUEST

            participant.device_serial = None
            participant.save()

            participant.spotify_account = None
            participant.save()

            self.logger.info(f"Participant {participant_pid} is no longer assigned an account and a device")

            return {"message": "Resource were successfully unpair from participant"}, HTTPStatus.OK    

        else:
            return {"message":"You are not allowed to disassociate resources from participants"}, HTTPStatus.FORBIDDEN


class ParticipantActiveResource(Resource):

    """
    TODO
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def patch(self, participant_pid):
        """
        
        """

        current_user = User.get_by_id(id=get_jwt_identity())

        if current_user.is_superuser or current_user.is_admin:

            participant = Participant.get_by_pid(pid=participant_pid)

            if participant is None:
                return {'message': 'Participant not found in DB'}, HTTPStatus.NOT_FOUND

            if (not participant.is_active) and (participant.device_serial is None or participant.spotify_account is None):
                return {'message':'There is no device or spotify account linked to this participant.'}, HTTPStatus.CONFLICT

            participant.is_active = not participant.is_active         
            participant.save()

            self.logger.info(f"Participant {participant.pid} active status: {participant.is_active}")
            
            return {'message': f'Participant {participant.pid} is now {participant.is_active}'}, HTTPStatus.OK
        else:
            return {'message':'You are not allowed to change this value'}, HTTPStatus.FORBIDDEN

        
