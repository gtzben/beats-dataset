"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-12-03
"""
import os, requests
import pandas as pd
from functools import wraps
from flask import render_template, flash, url_for, session, request, redirect
from . import survey_bp

from http import HTTPStatus
from app.routes.survey.forms import ParticipantLoginForm, PreStudy_Psychometrics, PostStudy_Psychometrics
from wtforms import RadioField

PSCYHOMETRICS_DIR = os.path.join(os.path.abspath("."),"data", "raw", "psychometrics")

TIPI_HEADERS = ["Statement", "1\nDisagree strongly", "2\nDisagree moderately", "3\nDisagree a little",
                "4\nNeither agree nor disagree", "5\nAgree a little", "6\nAgree moderately",
                "7\nAgree strongly"]

PANAS_HEADERS = ["Statement", "1\nVery slighlty or not at all", "2\nA little", "3\nModerately", "4\nQuite a bit", "5\nExtremely"]

PSS_HEADERS = ["Statement", "1\nNever", "2\nAlmost Never", "3\nSometimes", "4\nFairly Often", "5\nVery Often"]

PHQ9_HEADERS = ["Statement", "1\nNot at all", "2\nSeveral days", "3\nMore than half the days", "4\nNearly every day"]

STOMPR_HEADERS = ["Statement", "1\nDislikes strongly", "2\nDislike moderately", "3\nDislike a little", "4\nNeither like or dislike",
                                   "5\nLike a little", "6\nLike moderately", "7\nLike strongly"]

GSM_HEADERS = ["Statement", "1\nCompletly disagree", "2\nStrongly disagree", "3\nDisagree", "4\nNeither agree nor disagree",
                                "5\nAgree", "6\nStrongly agree", "7\nCompletely agree"]

DEMO_INTSR = ("In this section, we will ask about your gender, age, and other demographic details " +
              "to better understand who is participating in our study.",
              "This helps us see how the results apply to different groups of people.",
              "Your answers will remain anonymous, and for some question, you can decide whether to share the requested information or not.")

TIPI_INTSR = ("Here are a number of personality traits that may or may not apply to you.",
              "Select the option that best represents how much you agree or disagree with "+
              "the statement (1 = strongly disagree, 7 = strongly agree)")

PANAS_INTSR = ("Review the list of feelings and emotions.",
               "Choose the option that best describes the extent "
               "to which you have felt each emotion in the past week (1 = very slightly or not at all, 5 = extremely)")

PSS_INTSR = ("The questions below ask about your feelings and thoughts over the past month.",
             "Select how often you felt this way (1 = never, 5 = very often).")

PHQ9_INTSR = ("Over the last two weeks, how often have you been bothered by the following problems?",
              "Choose the option that best represents your experience (1 = not at all, 4 = nearly every day).")

STOMPR_INTSR = ("Read each music genre or statement about preferences",
                "Select how much you enjoy or agree with each (1 = strongly dislike, 7 = strongly like).")

GMS_INTSR = ("Answer each question about your musical habits, skills, and experiences.",
             "Use the provided scale to rate your response for each statement (1 = completly agree, 7 = completly disagree).")

FOLLOWUP_INTSR = ("Please let us know if you’d be interested in participating in a follow-up study.",
                  "Your response will also indicate whether we may contact you if there are findings " +
                  "we’d like to explore further about music listening for supporting health and well-being.")

def clear_blueprint_session(namespace):
    keys_to_clear = [key for key in session.keys() if key.startswith(namespace)]
    for key in keys_to_clear:
        session.pop(key)

@survey_bp.route('/login', methods=["GET", "POST"])
def login():

    flash("Please enter your Participant ID (PID) and email to proceed.", "info")

    form = ParticipantLoginForm()

    if form.validate_on_submit():

        session.pop('_flashes', None)

        data = {
        "pid": form.pid.data,
        "email": form.email.data
        }

        # sending post request and saving response as response object
        response = requests.post(url=url_for("api.participantlogin", _external=True), json=data)
        api_data = response.json()

        if response.status_code == HTTPStatus.OK:
            # Save info in session
            session[f'{request.blueprint}_participant_id'] = api_data["id"]
            session[f'{request.blueprint}_participant_pid'] = data["pid"]
            session[f'{request.blueprint}_is_active'] = api_data['is_active']
            session[f'{request.blueprint}_is_withdrawn'] = api_data['is_withdrawn']
            session[f'{request.blueprint}_is_completed'] = api_data['is_completed']

            flash('Login successful!', 'success')

            # Fill questionnaire to activate if not active, withdrawn and completed
            if not api_data['is_active'] and not (api_data['is_withdrawn'] or api_data['is_completed']):
                return redirect(url_for('survey.pre_study'))
            elif (api_data['is_withdrawn'] or api_data['is_completed']): # Conclude experiment if withdrawn or completed
                return redirect(url_for('survey.post_study'))
            else:
                clear_blueprint_session(request.blueprint) # Conditions not met to proceed
                flash("The participant has not completed the experiment. If he/she no longer wishes to continue, he/she must withdraw.","danger")
                return redirect(url_for('survey.login'))
            
        elif response.status_code in [HTTPStatus.UNAUTHORIZED,HTTPStatus.FORBIDDEN, HTTPStatus.CONFLICT]:
            flash(api_data["message"], 'danger')
        else:
            flash('An error occurred. Please try again later.', 'danger')

    return render_template('login_participant.html', title='Participant Sign In', form=form, logged_in=bool(session.get(f'{request.blueprint}_participant_pid')))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if f'{request.blueprint}_participant_pid' not in session:
            flash("You must log in first.", "danger")
            return redirect(url_for('survey.login'))  # Redirect to login if not authenticated
        return f(*args, **kwargs)
    return decorated_function

@survey_bp.route('/logout')
@login_required
def logout():
    clear_blueprint_session(request.blueprint)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('survey.login'))


@survey_bp.route('/pre-study', methods=["GET", "POST"])
@login_required
def pre_study():
    """
    
    """

    form = PreStudy_Psychometrics()
    total_pages = 8  # Number of pages in the form    

    # Define a mapping of pages to subforms
    page_config = {
        2: {'subform': form.demo, 'session_key': f'{request.blueprint}_demo_data'},
        3: {'subform': form.tipi, 'session_key': f'{request.blueprint}_tipi_data'},
        4: {'subform': form.panas, 'session_key': f'{request.blueprint}_panas_data'},
        5: {'subform': form.pss, 'session_key': f'{request.blueprint}_pss_data'},
        6: {'subform': form.phq9, 'session_key': f'{request.blueprint}_phq9_data'},
        7: {'subform': form.stompr, 'session_key': f'{request.blueprint}_stompr_data'},
        8: {'subform': form.gms, 'session_key': f'{request.blueprint}_gms_data'}
    }

    table_headers = {f"{request.blueprint}_demo_data": [],
                    f"{request.blueprint}_tipi_data": TIPI_HEADERS,
                    f"{request.blueprint}_panas_data": PANAS_HEADERS,
                    f"{request.blueprint}_pss_data": PSS_HEADERS,
                    f"{request.blueprint}_phq9_data": PHQ9_HEADERS,
                    f"{request.blueprint}_stompr_data":STOMPR_HEADERS,
                    f"{request.blueprint}_gms_data": GSM_HEADERS}
    
    survey_instructions = {f"{request.blueprint}_demo_data": DEMO_INTSR,
                           f"{request.blueprint}_tipi_data": TIPI_INTSR,
                           f"{request.blueprint}_panas_data": PANAS_INTSR,
                           f"{request.blueprint}_pss_data": PSS_INTSR,
                           f"{request.blueprint}_phq9_data": PHQ9_INTSR,
                           f"{request.blueprint}_stompr_data":STOMPR_INTSR,
                           f"{request.blueprint}_gms_data":GMS_INTSR}

    # Get current page from form data or default to the first page
    current_page = int(form.current_page.data) if request.method == 'POST' else 1
    if ('Back' in request.form):
        for dict_values in page_config.values():
            if dict_values["session_key"] in session:
                for field_name, field_value in session[dict_values["session_key"]].items():
                    getattr(dict_values["subform"], field_name).process(None, data=field_value)

    
    if request.method == 'POST':
        # Validate only the current page's subform
        if current_page in page_config:
            subform = page_config[current_page]['subform']
            session_key = page_config[current_page]['session_key']
            
            # Save valid data to session
            session[session_key] = subform.data
                
        if form.errors:
            # If there are errors, stay on the current page
            return render_template('pre_study.html', title='Pre-study',current_page=current_page,
                           form=form, subform_headers=subform_headers, subform_values=subform_values,
                           subform_instructions=subform_instructions, 
                           logged_in=bool(session.get(f'{request.blueprint}_participant_pid')))

        # Handle page navigation
        if 'Next' in request.form and current_page < total_pages:
            current_page += 1
        elif 'Back' in request.form and current_page > 1:
            current_page -= 1
        elif 'Submit' in request.form and current_page == total_pages:
            # Process and handle form submission
            collected_data = {key: session.get(key, {}) for key in [f'{request.blueprint}_demo_data',
                                                                    f'{request.blueprint}_tipi_data',
                                                                    f'{request.blueprint}_panas_data',
                                                                    f'{request.blueprint}_pss_data',
                                                                    f'{request.blueprint}_phq9_data',
                                                                    f'{request.blueprint}_stompr_data',
                                                                    f'{request.blueprint}_gms_data']}
            for key in collected_data:
                collected_data[key].pop('csrf_token', None)

            # Send str values and concatenate multi-values items in demographic data
            for q_item, q_resp in collected_data[f'{request.blueprint}_demo_data'].items():
                if isinstance(q_resp, list):
                    collected_data[f'{request.blueprint}_demo_data'][q_item] = "&".join(q_resp)

             # sending post request and saving response as response object
            response = requests.post(url=url_for("api.surveyresponsesresource", _external=True,
                                                  participant_pid=session.get(f'{request.blueprint}_participant_pid')), json=collected_data)
            api_data = response.json()

            if response.status_code == HTTPStatus.OK:
                # Save tokens in the session
                flash(api_data["message"], 'success')
                current_page += 1 # Final - Submitted

                # Create psychometrics directory if not exists
                os.makedirs(PSCYHOMETRICS_DIR, exist_ok=True)

                # Iterate surveys data
                for key_survey, value_response in collected_data.items():
                    str_item = list(value_response.keys())
                    for item_question in str_item: # rename columns to only integer value
                        value_response[int(item_question.split("_")[1])] = value_response.pop(item_question)
                    survey_record = pd.DataFrame.from_records([value_response]) # Turn into single row dataframe
                    survey_record = survey_record[sorted(survey_record.columns)] # sort columns numerically
                    survey_record.rename(columns=lambda col: f"item_{col}", inplace=True) # turn to string and add prefix and rename index
                    survey_record.rename(index={0: f"P{str(session[f'{request.blueprint}_participant_id']).zfill(2)}"}, inplace=True) 
                    survey_record.index.name = "participant_id"

                    # If psychometrics file exist add new record
                    survey_file = os.path.join(PSCYHOMETRICS_DIR, key_survey.split("_")[1] + ".csv")
                    if os.path.exists(survey_file):
                        df_survey = pd.read_csv(survey_file, index_col=0)
                        df_survey = pd.concat([df_survey, survey_record])
                        df_survey.to_csv(survey_file)
                    else: # Otherwise create file
                        survey_record.to_csv(survey_file)

            elif response.status_code == HTTPStatus.BAD_REQUEST:
                flash(api_data["message"], 'danger')
            elif response.status_code == HTTPStatus.CONFLICT:
                flash(api_data["message"], 'danger')
                return redirect(url_for('survey.logout'))
            else:
                flash('An error occurred. Please try again later.', 'danger')


        form.current_page.data = str(current_page)  # Update the current page

    else:
        # Initialize the form on the first GET request
        form.current_page.data = "1"
    
    #
    if ('Next' in request.form):
        for dict_values in page_config.values():
            if dict_values["session_key"] in session:
                for field_name, field_value in session[dict_values["session_key"]].items():
                    getattr(dict_values["subform"], field_name).process(None, data=field_value)

    #
    if current_page in page_config:
        subform = page_config[current_page]['subform']
        subform_values = []
        for field_name, field_obj in subform._fields.items():  # Access subform fields
            row = [field_obj.label.text] # Add label and field object
            if not isinstance(field_obj, RadioField):
                continue
            if field_obj.label.text == "CSRF Token":
                row.append(field_obj)
            else:
                radios = [o for o in field_obj]
                row.extend(radios)
                subform_values.append(row)

        subform_headers = table_headers[page_config[current_page]["session_key"]]
        subform_instructions = survey_instructions[page_config[current_page]["session_key"]]
    else:
        subform_values, subform_headers , subform_instructions = None, None, None

    # Render only the fields for the current page
    return render_template('pre_study.html', title='Pre-study', current_page=current_page,
                           form=form, subform_headers=subform_headers, subform_values=subform_values,
                           subform_instructions=subform_instructions, logged_in=bool(session.get(f'{request.blueprint}_participant_pid')))



@survey_bp.route('/post-study', methods=["GET", "POST"])
@login_required
def post_study():
    """
    
    """

    if session.get(f'{request.blueprint}_is_withdrawn'):
        #
        response = requests.post(url=url_for("api.participantconcluderesource", _external=True,
                                             participant_pid=session.get(f'{request.blueprint}_participant_pid')))
        api_data = response.json()

        print(response)
        
        if response.status_code == HTTPStatus.OK:
            flash(api_data["message"], 'success')
            return render_template('opt_out.html', title='Opt out', blueprint=request.blueprint, logged_in=bool(session.get(f'{request.blueprint}_participant_pid')))
        
        elif response.status_code in [HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN, HTTPStatus.CONFLICT]:
            flash(api_data["message"], 'danger')
        else:
            clear_blueprint_session(request.blueprint)
            flash('An error occurred. Please try again later.', 'danger')

        return redirect(url_for('survey.login'))

    else:

        form = PostStudy_Psychometrics()
        total_pages = 5  # Number of pages in the form    

        # Define a mapping of pages to subforms
        page_config = {
            2: {'subform': form.panas, 'session_key': f'{request.blueprint}_panas_data'},
            3: {'subform': form.pss, 'session_key': f'{request.blueprint}_pss_data'},
            4: {'subform': form.phq9, 'session_key': f'{request.blueprint}_phq9_data'},
            5: {'subform': form.followup, 'session_key': f'{request.blueprint}_followup_data'}
        }

        table_headers = {f"{request.blueprint}_panas_data": PANAS_HEADERS,
                        f"{request.blueprint}_pss_data": PSS_HEADERS,
                        f"{request.blueprint}_phq9_data": PHQ9_HEADERS,
                        f"{request.blueprint}_followup_data": []}
        
        survey_instructions = {

                            f"{request.blueprint}_panas_data": PANAS_INTSR,
                            f"{request.blueprint}_pss_data": PSS_INTSR,
                            f"{request.blueprint}_phq9_data": PHQ9_INTSR,
                            f"{request.blueprint}_followup_data":FOLLOWUP_INTSR}
        
        # If completed show final page
        if (not session.get(f'{request.blueprint}_is_active')) and session.get(f'{request.blueprint}_is_completed'):
            current_page = 6
        else: # Get current page from form data or default to the first page
            current_page = int(form.current_page.data) if request.method == 'POST' else 1

        if ('Back' in request.form):
            for dict_values in page_config.values():
                if dict_values["session_key"] in session:
                    for field_name, field_value in session[dict_values["session_key"]].items():
                        getattr(dict_values["subform"], field_name).process(None, data=field_value)

        
        if request.method == 'POST':
            # Validate only the current page's subform
            if current_page in page_config:
                subform = page_config[current_page]['subform']
                session_key = page_config[current_page]['session_key']
                
                # Save valid data to session
                session[session_key] = subform.data
                    
            if form.errors:
                # If there are errors, stay on the current page
                return render_template('post_study.html', title='Post-study',current_page=current_page,
                            form=form, subform_headers=subform_headers, subform_values=subform_values,
                            subform_instructions=subform_instructions, 
                            logged_in=bool(session.get(f'{request.blueprint}_participant_pid')))

            # Handle page navigation
            if 'Next' in request.form and current_page < total_pages:
                current_page += 1
            elif 'Back' in request.form and current_page > 1:
                current_page -= 1
            elif 'Submit' in request.form and current_page == total_pages:
                # Process and handle form submission
                collected_data = {key: session.get(key, {}) for key in [f'{request.blueprint}_panas_data',
                                                                        f'{request.blueprint}_pss_data',
                                                                        f'{request.blueprint}_phq9_data',
                                                                        f'{request.blueprint}_followup_data']}
                for key in collected_data:
                    collected_data[key].pop('csrf_token', None)

                # Get followup single value
                collected_data[f'{request.blueprint}_followup_data'] = next(iter(collected_data[f'{request.blueprint}_followup_data'].values()))
                
                # sending post request and saving response as response object
                response = requests.post(url=url_for("api.participantconcluderesource", _external=True,
                                                    participant_pid=session.get(f'{request.blueprint}_participant_pid')), json=collected_data)
                api_data = response.json()

                if response.status_code == HTTPStatus.OK:
                    # Save tokens in the session
                    flash(api_data["message"], 'success')
                    current_page += 1 # Final - Submitted

                    # Create psychometrics directory if not exists
                    os.makedirs(PSCYHOMETRICS_DIR, exist_ok=True)

                    # Followup no psychometrics. Remove 
                    collected_data.pop(f'{request.blueprint}_followup_data', None)

                    # Iterate surveys data
                    for key_survey, value_response in collected_data.items():
                        str_item = list(value_response.keys())
                        for item_question in str_item: # rename columns to only integer value
                            value_response[int(item_question.split("_")[1])] = value_response.pop(item_question)
                        survey_record = pd.DataFrame.from_records([value_response]) # Turn into single row dataframe
                        survey_record = survey_record[sorted(survey_record.columns)] # sort columns numerically
                        survey_record.rename(columns=lambda col: f"item_{col}", inplace=True) # turn to string and add prefix and rename index
                        survey_record.rename(index={0: f"P{str(session[f'{request.blueprint}_participant_id']).zfill(2)}"}, inplace=True) 
                        survey_record.index.name = "participant_id"

                        # If psychometrics file exist add new record
                        survey_file = os.path.join(PSCYHOMETRICS_DIR, "post_"+key_survey.split("_")[1] + ".csv")
                        if os.path.exists(survey_file):
                            df_survey = pd.read_csv(survey_file, index_col=0)
                            df_survey = pd.concat([df_survey, survey_record])
                            df_survey.to_csv(survey_file)
                        else: # Otherwise create file
                            survey_record.to_csv(survey_file)

                elif response.status_code == HTTPStatus.BAD_REQUEST:
                    flash(api_data["message"], 'danger')
                elif response.status_code == HTTPStatus.CONFLICT:
                    flash(api_data["message"], 'danger')
                    current_page = 6
                    # return redirect(url_for('survey.logout'))
                else:
                    flash('An error occurred. Please try again later.', 'danger')

            form.current_page.data = str(current_page)  # Update the current page

        else:
            # Initialize the form on the first GET request
            form.current_page.data = "1"
        
        #
        if ('Next' in request.form):
            for dict_values in page_config.values():
                if dict_values["session_key"] in session:
                    for field_name, field_value in session[dict_values["session_key"]].items():
                        getattr(dict_values["subform"], field_name).process(None, data=field_value)

        #
        if current_page in page_config:
            subform = page_config[current_page]['subform']
            subform_values = []
            for field_name, field_obj in subform._fields.items():  # Access subform fields
                row = [field_obj.label.text] # Add label and field object
                if not isinstance(field_obj, RadioField):
                    continue
                if field_obj.label.text == "CSRF Token":
                    row.append(field_obj)
                else:
                    radios = [o for o in field_obj]
                    row.extend(radios)
                    subform_values.append(row)

            subform_headers = table_headers[page_config[current_page]["session_key"]]
            subform_instructions = survey_instructions[page_config[current_page]["session_key"]]
        else:
            subform_values, subform_headers , subform_instructions = None, None, None

        # print(session.get(f'{request.blueprint}_followup_data'))

        # Render only the fields for the current page
        return render_template('post_study.html', title='Post-study', current_page=current_page,
                            form=form, subform_headers=subform_headers, subform_values=subform_values,
                            subform_instructions=subform_instructions, logged_in=bool(session.get(f'{request.blueprint}_participant_pid')))