"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-12-04
"""
import re
from marshmallow import Schema, fields, ValidationError


def validate_survey_responses(responses_dict, survey_name):
    """
    Validates that the keys in the responses_dict follow the expected pattern
    for survey item names, and that their corresponding values are strings.
    -------------
    Intputs:
        responses_dict(dict): A dictionary where keys are questionnaire item names and values are the responses.
        survey_name(str): 
    Outputs:
        None
    """

    valid_surveys = ["demo", 'panas', 'pss', 'phq9', 'tipi', 'gms', 'stompr']
    if survey_name not in valid_surveys:
        raise ValidationError(f"Invalid survey name '{survey_name}'. Must be one of {valid_surveys}.")

    item_pattern = re.compile(rf"^{survey_name}_\d+$")

    for item, value in responses_dict.items():
        if type(value) is not str:
            raise ValidationError(f"The response value for '{item}' must be a string, but got {type(value).__name__}.")
        if not (re.search(item_pattern, item)):
            raise ValidationError(f"Invalid item name '{item}'. Each item name must follow the pattern: {survey_name}_<item_number>.")


class PreSurveySchema(Schema):
    survey_demo_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "demo"))
    survey_tipi_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "tipi"))
    survey_panas_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "panas"))
    survey_pss_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "pss"))
    survey_phq9_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "phq9"))
    survey_stompr_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "stompr"))
    survey_gms_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "gms"))

class PostSurveySchema(Schema):
    survey_panas_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "panas"))
    survey_pss_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "pss"))
    survey_phq9_data = fields.Dict(validate=lambda responses_dict: validate_survey_responses(responses_dict, "phq9"))
    survey_followup_data = fields.Boolean(required=True)