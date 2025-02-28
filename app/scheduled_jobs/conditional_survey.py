
import os, click, logging, traceback

import pandas as pd
from datetime import datetime

from requests.models import PreparedRequest


from flask import current_app, render_template
from flask.cli import with_appcontext
from flask_mail import Message


from app.utils import decrypt_email, setup_periodic_jobs_logger, handle_error_notification
from app.extensions import mail

from app.routes.api.models.music import MusicListening
from app.routes.api.models.participant import Participant

from app.routes.api.schemas.music import MusicListeningSchema
from app.routes.api.schemas.participant import ParticipantFlatSchema



#
LOGGER =logging.getLogger("survey_distribution")
ERROR_FLAG_FILE = "data/locks/.lock-email-error-survey-{date}"




def _concat_strings(items):
    if len(items) <= 1:
        return ''.join(items)
    if len(items) == 2:
        return ' and '.join(items)
    return '{}, and {}'.format(', '.join(items[:-1]), items[-1])

@with_appcontext
def distribute_conditional_survey(hours_offset):
    """
    
    """


    participant_obj = Participant.get_all_participants(is_active=True, is_withdrawn=False)
    active_participants = ((ParticipantFlatSchema(many=True, only=["id", "pid", "spotify_account"])
                           .dump(participant_obj))
                           .get("data"))
    
    uri_study_playlists = [pl 
                           for lst_pl in current_app.config["STUDY_PLAYLISTS"].values()
                           for pl in lst_pl] 
    
    for participant in active_participants:
    
        # Check by active participants
        id_participant, pid, spotify_account = participant.values()

        # Uniform naming convention to store participants data in independent directories 
        id_participant = f"P{str(id_participant).zfill(2)}"

        recent_tracks_obj = MusicListening.get_recent_listening(pid, uri_study_playlists, hours_offset)
        participant_recent_tracks = ((MusicListeningSchema(many=True, 
                                        only=["listening_session_id", "track_uri", "context","context_uri"])
                                    .dump(recent_tracks_obj))
                                    .get("data"))
        if len(participant_recent_tracks)==0:
            LOGGER.debug(f"Participant {id_participant} did not listen to study playlist during the last {hours_offset} hours")
            continue
        
        df_recent_tracks = pd.DataFrame(participant_recent_tracks)  

        sessions = list(df_recent_tracks["listening_session_id"].unique())
        context_counts = df_recent_tracks.groupby("context").size().to_dict()
        study_playlist_listened = list(df_recent_tracks["context_uri"].map(current_app.config["PLAYLISTS_URI_NAME"]).unique())        
        
        LOGGER.debug(f"Participant {id_participant} listened to music for {context_counts} during session(s) {sessions} by playing {study_playlist_listened} playlists.")
        
        # Send email
        subject = 'BEATS Study - Please answer a quick survey!'
        survey_type = "Study Playist Survey" 
        title = f"{survey_type} - Function(s) {_concat_strings(list(context_counts.keys()))}"
        greetings = f'Dear Participant {pid},'
        first_sentence = f'We noticed you recently listened to the following playlist(s):'
        next_steps = 'Please take a moment to answer a few questions about your experience by clicking the button below:'
        button = "Take the Survey"

        participant_email = decrypt_email(Participant.get_by_linked_spotify(spotify_account).email_encrypted)

        req = PreparedRequest()
        params = {"ID":id_participant, "PID":pid, "Sessions":sessions, "Functions": list(context_counts.keys()),
                  "Playlists":study_playlist_listened}
        req.prepare_url(current_app.config["SURVEY_LINK"], params)

        with mail.connect() as conn:
            subject = subject
            msg = Message(subject=subject,
                        recipients=[participant_email],
                        html=render_template("email_template.html", 
                        title=title,
                        greetings=greetings,
                        first_sentence=first_sentence,
                        important_info=_concat_strings(study_playlist_listened),
                        next_steps=next_steps,
                        button=button,
                        link=req.url,
                        show_link=False))

            try:
                conn.send(msg)
                LOGGER.info(f"Survey sent to participant {pid}")
            except Exception:
                LOGGER.exception(f"Unable to send survey email to {pid}")
                raise
    return


@with_appcontext
def __send_error_email(error_message):
    """

    """

    subject = 'BEATS Study - Error Running Daily Script'
    title = "Immediate Attention Required"
    greetings = f'Dear Experimenter,'
    first_sentence = 'An error has occurred while running daily periodic jobs. The app may not be functioning correctly.'
    next_steps = f'Error Details: {error_message}'
    button = ""
    link = ""

    with mail.connect() as conn:
        subject = subject
        msg = Message(subject=subject,
                      recipients=[current_app.config["ERROR_EMAIL"]],
                      html=render_template("email_template.html", 
                      title=title,
                      greetings=greetings,
                      first_sentence=first_sentence,
                      important_info="",
                      next_steps=next_steps,
                      button=button,
                      link=link,
                      show_link=False))

        try:
            conn.send(msg)
            LOGGER.exception("Error email sent to experimenter")
        except Exception:
            LOGGER.exception(f"Unable to send error email")


def _handle_error_notification(error_message, error_file):
    """
    Sends an email notification only once per issue using a flag file.
    """
    if not os.path.exists(error_file):
        __send_error_email(error_message)  # Replace with actual email function
        with open(error_file, "w") as f:
            f.write(f"Error reported: {error_message}")


@click.command()
@click.option("--hours_offset", default=12, help='Number of hours to check music activity')
def run_survey_distribution(hours_offset):
    """
    Execute daily jobs
    """
    global ERROR_FLAG_FILE

    error_date = ERROR_FLAG_FILE.format(date=datetime.today().date())

    #
    global LOGGER
    survey_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "logs", f"survey_distribution.log")
    LOGGER = setup_periodic_jobs_logger(survey_log_path, LOGGER)

    #
    try:
        distribute_conditional_survey(hours_offset)
    except Exception as e:
        error_date_job = error_date.format(daily_job="purge")
        error_details = {"subject":'BEATS Study - Error Survey Distribution',
                         "first_sentence": 'An error has occurred while sending survey to participants. The app may not be functioning correctly.',
                         "error_message": e}
        handle_error_notification(error_details, error_date_job, LOGGER)
        LOGGER.error(
        "An error occurred while distributing surveys:\n"
        f"Exception: {e}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )
        
