"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from http import HTTPStatus
from marshmallow import ValidationError

from flask import current_app, request

from flask_restful import Resource

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.routes.api.schemas.survey import SurveySchema
from app.routes.api.models.survey import Question, Questionnaire, Response
from app.routes.api.models.participant import Participant


class SurveyResponsesResource(Resource):
    
    """
    TODO
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def get(self):
        """
        
        """


        return


    def post(self, participant_pid):
        """
        TODO
        """

        #
        json_data = request.get_json()

        #
        try:
            survey_data = SurveySchema().load(json_data)
        except ValidationError as errors:
            return {'message': 'Validation errors', 'errors':errors.messages}, HTTPStatus.BAD_REQUEST
        
        participant = Participant.get_by_pid(participant_pid)

        if participant.is_active:
            return {'message': 'Participant is already active and has already completed the questionnaires'}, HTTPStatus.CONFLICT
           
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

        #
        
        participant.is_active=True
        participant.save()

        self.logger.debug(f"Participant {participant_pid} has completed the questionnaires and now is active.")

        return {"message":"Responses were received successfully!"}, HTTPStatus.OK