"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""
import os
import shutil

import pandas as pd

from http import HTTPStatus

from flask import current_app, request, make_response, render_template, url_for
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required

from marshmallow import ValidationError
from app.routes.api.schemas.participant import ParticipantSchema, ParticipantFlatSchema
from app.routes.api.schemas.link import LinkSchema
from app.routes.api.schemas.survey import PostSurveySchema

from app.routes.api.models.user import User
from app.routes.api.models.participant import Participant
from app.routes.api.models.device import Device
from app.routes.api.models.spotifyaccount import SpotifyAccount
from app.routes.api.models.survey import Questionnaire, Response



from app.utils import generate_token, verify_token, send_email, encrypt_email, hash_email, decrypt_email

DATASET_DIR = os.path.join(os.path.abspath("."),"data", "raw")

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

            return data, HTTPStatus.OK
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
            greetings = f'Dear Participant {participant.pid},'
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

            self.logger.info(f"User {current_user.email} has registered participant {participant.pid}! Pending for email validation.")

            return participant_created, HTTPStatus.CREATED
        
        else:
            return {"message":"You are not allowed to sign up participants"}, HTTPStatus.FORBIDDEN

def parse_boolean(value):
    # Flask doesn't automatically interpret "false" as a boolean
    # when passing a parameter in a URL query string
    # to contemplate absence as None and false as False use this function
    if value is None:
        return None  # Parameter not passed
    if value.lower() in ["true", "1", "yes"]:
        return True
    if value.lower() in ["false", "0", "no"]:
        return False
    return None     

class ParticipantPortal(Resource):

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
                
                data = ParticipantFlatSchema().dump(participant)

            else:
                is_active = parse_boolean(request.args.get("is-active"))
                is_verified = parse_boolean(request.args.get("is-verified"))
                is_withdrawn = parse_boolean(request.args.get("is-withdrawn"))
                is_completed = parse_boolean(request.args.get("is-completed"))
                all_participants = Participant.get_all_participants(is_active=is_active, is_verified=is_verified,
                                                                     is_withdrawn=is_withdrawn, is_completed=is_completed)
                data = (ParticipantFlatSchema(many=True, exclude=("device_serial", "spotify_account", "is_verified", "updated_at"))
                        .dump(all_participants))

            return data, HTTPStatus.OK
        else:
            return {"message":"You are not allowed to see this information"}, HTTPStatus.FORBIDDEN
        

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

        self.logger.info(f"Participant {participant.pid} has been verified!")

        return make_response(render_template('confirm_token.html', title="Account Verified",confirm='Your account has been successfully verified.'), HTTPStatus.OK, {'Content-Type': 'text/html'})
    

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

            if not participant.is_active:
                return {'message': "Participant must be active to assign resources"}, HTTPStatus.BAD_REQUEST

            if data.get('serial_number'):
                # if Participant.get_by_linked_device(serial_number=data.get('serial_number')):
                device = Device.get_by_serial(serial=data.get('serial_number'))
                if device is None:
                    return {'message': f"The device {data.get('serial_number')} is not in the DB"}, HTTPStatus.BAD_REQUEST

                if device.is_assigned:
                    return {'message': f"The device {data.get('serial_number')} has already being assigned"}, HTTPStatus.BAD_REQUEST
                
                if participant.device_serial:
                    already_assigned_device = Device.get_by_serial(serial=participant.device_serial)
                    already_assigned_device.is_assigned = False
                    already_assigned_device.save()
                
                participant.device_serial = data.get('serial_number')
                participant.device_id= device.id
                participant.save()
                device.is_assigned = True
                device.save()

            if data.get('account_email'):
                # if Participant.get_by_linked_device(serial_number=data.get('serial_number')):
                spotify_account = SpotifyAccount.get_by_email(email=data.get('account_email'))
                if spotify_account is None:
                    return {'message': f"The account {data.get('account_email')} is not in the DB"}, HTTPStatus.BAD_REQUEST

                if spotify_account.is_assigned:
                    return {'message': f"The account {data.get('account_email')} has already being assigned"}, HTTPStatus.BAD_REQUEST
                
                if participant.spotify_account:
                    already_assigned_spotify = SpotifyAccount.get_by_email(email=participant.spotify_account)
                    already_assigned_spotify.is_assigned = False
                    already_assigned_spotify.save()
                
                participant.spotify_account = data.get('account_email')
                participant.spotify_id = spotify_account.id
                participant.save()
                spotify_account.is_assigned = True
                spotify_account.save()


            self.logger.info(f"Device {participant.device_serial} and account {participant.spotify_account} are linked to participant {participant_pid}.")

            return {"message": f"Resource association to participant {participant_pid} was successful"}, HTTPStatus.OK    

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

            if not participant.is_active:
                return {'message': "Unable to unlink resources since participant has already finished data collection"}, HTTPStatus.BAD_REQUEST
            
            if participant.device_serial is not None:
                device = Device.get_by_serial(serial=participant.device_serial)
                device.is_assigned = False
                device.save()
                participant.device_serial = None
                participant.save()

            if participant.spotify_account is not None:
                spotify_account = SpotifyAccount.get_by_email(email=participant.spotify_account )
                spotify_account.is_assigned = False
                spotify_account.save()
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

            if (participant.is_active) and (participant.device_serial is None or participant.spotify_account is None):
                return {'message':'There is no device or spotify account linked to this participant.'}, HTTPStatus.CONFLICT

            participant.is_active = not participant.is_active         
            participant.save()

            self.logger.info(f"Participant {participant.pid} active status: {participant.is_active}")
            
            return {'message': f'Participant {participant.pid} is now {participant.is_active}'}, HTTPStatus.OK
        else:
            return {'message':'You are not allowed to change this value'}, HTTPStatus.FORBIDDEN
        

class ParticipantLogin(Resource):

    """
    TODO
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger


    def post(self):
        """
        
        """

        json_data = request.get_json()

        try:
            data = ParticipantSchema(only=('pid','email')).load(json_data)
        except ValidationError as errors:
            return {'message': 'Validation errors', 'errors': errors.messages}, HTTPStatus.BAD_REQUEST
        
        pid = data.get("pid")
        email = data.get("email")

        participant = Participant.get_by_pid(pid=pid)

        if (participant is None) or (email != decrypt_email(participant.email_encrypted)):
            return {'message':'PID or password is incorrect'}, HTTPStatus.UNAUTHORIZED
        
        if participant.is_verified is False:
            return {'message': 'The participant account is not verified yet'}, HTTPStatus.FORBIDDEN\
        
        if not participant.is_active and not (participant.is_withdrawn or participant.is_completed):
            self.logger.info(f"Participant {pid} has sign in for the pre-study flow!")
        elif (not participant.is_active) and (participant.is_withdrawn):
            self.logger.info(f"Participant {pid} has opted out and has returned device already")
            return {"message": "Participant opted out and device returned already."}, HTTPStatus.CONFLICT      
        elif participant.is_withdrawn or participant.is_completed: # Conclude experiment if withdrawn or completed
            self.logger.info(f"Participant {pid} has sign in for the post-study flow!")
        else:
            self.logger.warning(f"Participant {pid} has not completed the experiment. If he/she no longer wishes to continue, he/she must withdraw.")
            return {"message": "Participant has not completed the experiment. Wait or opt out the experiment"}, HTTPStatus.CONFLICT
        
        return {"is_active":participant.is_active, "is_withdrawn":participant.is_withdrawn, "is_completed":participant.is_completed, "id":participant.id}, HTTPStatus.OK



class ParticipantWithdrawResource(Resource):

    """
    TODO
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def post(self, participant_pid):
        """
        
        """

        current_user = User.get_by_id(id=get_jwt_identity())

        if current_user.is_superuser or current_user.is_admin:

            participant = Participant.get_by_pid(pid=participant_pid)

            if participant is None:
                return {'message': 'Participant not found in DB'}, HTTPStatus.NOT_FOUND

            if participant.is_withdrawn:
                return {'message':'The participant has already whitdrawn from the experiment.'}, HTTPStatus.CONFLICT

            token = generate_token(participant.pid, salt='withdraw')

            subject = f"BEATS Study - Please, confirm {participant.pid} withdrawal"
            title = "Confirm Participant Withdrawal"
            greetings = f'Dear Experimenter,'
            thank_you = f'Participant {participant.pid} has requested to withdraw from the study and for the data collected from him/her to be excluded.'
            next_steps = 'To proceed with the request, click the link below. Once withdrawn, his/her data will no longer be part of the dataset. If a device is still assigned, an email will be sent to the participant to arrange a time to return the provided instruments.'
            button = "Confirm Withdrawal"
            link = url_for('api.participantexcluderesource',token=token,_external=True)

            #
            send_email(current_user.email,
                       subject,
                       'email_template.html',
                       participant.pid,
                       title=title,
                       greetings=greetings,
                       thank_you=thank_you,
                       next_steps=next_steps,
                       button=button,
                       link=link)
            
            return {'message': f'Check your email {current_user.email} to confirm that participant {participant.pid} will be excluded from the study.'}, HTTPStatus.OK
        else:
            return {'message':'You are not allowed to withdraw participants'}, HTTPStatus.FORBIDDEN
        

class ParticipantExcludeResource(Resource):
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
        withdraw_pid = verify_token(token, max_age=(60 * 60 * 24), salt='withdraw') # Token expires in 1 day

        if withdraw_pid is False:
            return {'message': 'Invalid token or token expired'}, HTTPStatus.BAD_REQUEST

        #
        participant = Participant.get_by_pid(withdraw_pid)

        if not participant:
            return {'message': 'Participant not found'}, HTTPStatus.NOT_FOUND

        if participant.is_withdrawn is True:
            return {'message': 'The participant has alredy been withdrawn'}, HTTPStatus.BAD_REQUEST
        
        #
        participant_id = f"P{str(participant.id).zfill(2)}"
        participant_dir = os.path.join(DATASET_DIR, participant_id)
        psychometrics_dir = os.path.join(DATASET_DIR, "psychometrics")

        try:
            if os.path.exists(participant_dir):
                shutil.rmtree(participant_dir, ignore_errors=True)
                self.logger.info(f"Participant data directory {participant_id} successfully removed from dataset")
        except Exception as e:
            self.logger.error(f"An error occured while deleting participant {participant_id} directory: {e}")

        
        if os.path.exists(psychometrics_dir):
            quest_responses = os.listdir(psychometrics_dir)
            for quest in quest_responses:
                csv_quest = os.path.join(psychometrics_dir, quest)
                try:
                    pd.read_csv(csv_quest, index_col=0).drop(participant_id, axis=0).to_csv(csv_quest)
                except Exception as e:
                    self.logger.error(f"An error occured while deleting participant {participant_id} psychometrics: {e}")
            self.logger.info(f"Participant {participant_id} responses removed from questionnaire files")

        # subject = f"BEATS Study - Arrange Meeting to Conclude Participation"
        # thank_you = f'Thank you for your valuable participation in the BEATS study. We appreciate your contribution to our research.'
        # title = "Conclude Participation"
        
        title = "Opt out Request Confirmed"
        greetings = f'Dear {withdraw_pid},'
        thank_you = f'Thank you for notifying us of your withdrawal from the BEATS study. Your request has been received, and your data will no longer be included in the study.'

        if participant.device_serial is None:
            subject = f"BEATS Study - Retroactive opt-out"
            next_steps = 'There are no further steps required for you. If you have any questions, please contact the experimenter. Thank you for your time and participation.'
            button = ""
            link = ""
        else: # Request to return device if there is a device assigned to participant
            subject = f"BEATS Study - Opting out and Arrange Meeting to Return Device"
            next_steps = 'Please arrange a meeting to conclude the experiment and return the data collection instruments. Click the link below to schedule a convenient time.'
            button = "Schedule Meeting"
            link="https://calendly.com/2941451g-student/the-beats-dataset-study-completion-and-device-return"

        #
        participant_email = decrypt_email(participant.email_encrypted)
        send_email(participant_email,
                    subject,
                    'email_template.html',
                    withdraw_pid,
                    title=title,
                    greetings=greetings,
                    thank_you=thank_you,
                    next_steps=next_steps,
                    button=button,
                    link=link)

        self.logger.info(f"Withdrawal email sent to participant {withdraw_pid}. Device assigned to participant: {participant.device_serial}")

        participant.is_withdrawn = True
        participant.save()
        self.logger.info(f"Participant {withdraw_pid} has been excluded for the study!")

        return make_response(render_template('confirm_token.html',  title="Participant Withdrawal",confirm=f'Participant {withdraw_pid} withdrawal was successful'), HTTPStatus.OK, {'Content-Type': 'text/html'})
                
        
class ParticipantConcludeResource(Resource):

    """
    TODO
    
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    def post(self, participant_pid):

        participant = Participant.get_by_pid(participant_pid)

        if participant is None:
            return {'message': f"Participant {participant_pid} not found in DB"}, HTTPStatus.NOT_FOUND
        
        if not participant.is_verified:
            return {'message': "Participant has not been verified"}, HTTPStatus.BAD_REQUEST

        if (not participant.is_active) and participant.is_completed:
            return {'message': "Participant has already completed the experimental period and has already completed the post-study's questionnaires"}, HTTPStatus.CONFLICT
        
        if not participant.is_withdrawn:

            json_data = request.get_json()
            #
            try:
                survey_data = PostSurveySchema().load(json_data)
            except ValidationError as errors:
                self.logger.error(f"Validation error when submitting surveys data: {errors.messages}")
                return {'message': 'Validation errors', 'errors':errors.messages}, HTTPStatus.BAD_REQUEST
            
            # Update followup response to participant table 
            followup = survey_data.pop("survey_followup_data", False)
            participant.follow_up=followup
            self.logger.debug(f"Participant {participant_pid} interested in followup study? {followup}")

            #
            survey_responses = []
            for survey, responses in survey_data.items():
                survey_name = survey.split("_")[1]
                questions = Questionnaire.get_questions(name=survey_name)
                for q in questions:
                    q_item = f"{survey_name}_{q.n_item}"
                    response = {"participant_pid":participant_pid, "question_id":q.id, "response":responses[q_item]}
                    survey_responses.append(response)   
            #
            response_obj = Response()
            response_obj.bulk_insert(survey_responses)
        
        # Proceed by removing device and account
        if participant.device_serial is not None:
                device = Device.get_by_serial(serial=participant.device_serial)
                device.is_assigned = False
                device.save()
                participant.device_serial = None
                participant.save()

        if participant.spotify_account is not None:
            spotify_account = SpotifyAccount.get_by_email(email=participant.spotify_account )
            spotify_account.is_assigned = False
            spotify_account.save()
            participant.spotify_account = None
            participant.save()

        participant.is_active=False
        participant.save()

        self.logger.info(f"Participant {participant_pid} is no longer active and both device and account have been unlinked")

        return {"message": "Resource were successfully unpair from participant and is now innactive"}, HTTPStatus.OK 


        