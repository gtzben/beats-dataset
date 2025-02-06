import os, click, logging
import pandas as pd
from datetime import datetime, timedelta

from flask import current_app, render_template

from app.scheduled_jobs.connect_empatica_cloud import get_files_from_s3_ts_range

from app.routes.api.models.user import User
from app.routes.api.models.participant import Participant
from app.routes.api.models.music import MusicListening
from app.routes.api.models.spotifyaccount import SpotifyAccount

from app.routes.api.schemas.participant import ParticipantFlatSchema
from app.routes.api.schemas.music import MusicListeningSchema

from app.routes.api.resources.spotify import cache_dir

from app.utils import decrypt_email

from flask_mail import Message
from app.extensions import mail



from flask.cli import with_appcontext

#
LOGGER =logging.getLogger("scheduled_monitoring")

RAW_DIR = "data/raw"

def __setup_logger(daily_log_path):
    """
    
    """

    global LOGGER

    #
    LOGGER.setLevel(logging.DEBUG)

    #
    file_handler = logging.FileHandler(daily_log_path)

    # Create formatters and add them to handlers
    formatter = logging.Formatter("[%(levelname)s] - [%(asctime)s.%(msecs)03d] - %(name)s - %(filename)s:%(lineno)s - %(funcName)s(): message: %(message)s",
                                   datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    #
    LOGGER.addHandler(file_handler)

    return


@with_appcontext
def purge_cache_and_not_verified(max_days_users=1, max_days_participants = 21):
    """
    Delete users and participants whose account was not verified, as well as cache files not
    associated to Spotify accounts in DB
    """

    not_verified_users = User.get_all_users(is_verified=False)
    not_verified_participants = Participant.get_all_participants(is_verified=False)
    valid_cache_spotify = [account.cache_path for account in SpotifyAccount.get_all_accounts()]
    all_cache_spotify = [os.path.join(cache_dir,cache) for cache in os.listdir(cache_dir) if cache.startswith(".cache-")]

    for user in not_verified_users:
        delta_days = (datetime.now()-user.created_at).days
        if delta_days >= max_days_users:
            user.delete()
            LOGGER.info(f"User {user.email} was deleted from db since email verification expired")

    for participant in not_verified_participants:
        delta_days = (datetime.now()-participant.created_at).days
        if delta_days >= max_days_participants:
            participant.delete()
            LOGGER.info(f"Participant {participant.pid} was deleted from db since email verification expired")
    
    removed_cache=0
    for cache in all_cache_spotify:
        if cache not in valid_cache_spotify:
            os.remove(cache)
            removed_cache+=1
    LOGGER.info(f"Removed {removed_cache} cache files not linked to Spotify accounts in DB")


def daily_physio_transfer(id_participant, spotify_account, pid, device_serial, participant_dir, created_at,
                          start_end_sessions, date, last_session_ts):
    """
    
    """

    files_transfered = False

    # Only download if participant listened to music
    if len(start_end_sessions)>0:
        LOGGER.info(start_end_sessions)

        signals_session, timestamps, already_transferred = get_files_from_s3_ts_range(pid, device_serial, date, -float("inf"), float("inf"), last_session_ts, offset_minutes=0)

        if len(signals_session)>0:
            # Assign file name keeping original order
            # {start_ts_physio}_{end_ts_physio}_{observation_day}
            obs_day = (datetime.fromisoformat(date).date() - datetime.fromisoformat(created_at).date()).days
            save_dir = os.path.join(participant_dir, "_".join(map(str,[timestamps[0], timestamps[-1]]))+f"_{str(obs_day).zfill(2)}")
            name_files = ["accelerometer.csv", "gyroscope.csv", "eda.csv", "temperature.csv",
                            "bvp.csv", "steps.csv", "tags.csv", "systolicPeaks.csv"]
            
            os.makedirs(save_dir, exist_ok=True)

            #
            for df_signal, file_name in zip(signals_session, name_files):
                file_path = os.path.join(save_dir, file_name)
                df_signal.to_csv(file_path, index=False)

                # Use eda timestamps as reference
                # no particular purpose
                if file_name == "eda.csv":
                    signal_start = df_signal["unix_timestamp"].min()
                    signal_end = df_signal["unix_timestamp"].max()

            #
            df_tracks_daily = pd.DataFrame()
            for music_session in start_end_sessions:
                session_id, _, _ = music_session.values()
                tracks_obj = MusicListening.get_by_pid_session_id(pid, session_id)
                tracks_session = MusicListeningSchema(many=True, only=["listening_session_id", "track_session_id", "track_name","track_uri", "context",
                                                                    "device_type", "playback_inconsistency" ,"started_at", "ended_at"]).dump(tracks_obj)["data"]
                df_tracks_session = pd.DataFrame.from_records(tracks_session)
                df_tracks_session["started_at"] = pd.to_datetime(df_tracks_session['started_at'], format='ISO8601').astype(int) // 10**3
                df_tracks_session['ended_at'] = pd.to_datetime(df_tracks_session['ended_at'], format='ISO8601').astype(int) // 10**3

                df_tracks_daily = pd.concat([df_tracks_daily, df_tracks_session]).reset_index(drop=True)

            # Get music session tracks within signal's timestamp range
            df_tracks_daily = df_tracks_daily[(df_tracks_daily["started_at"] >= signal_start) & 
                                        (df_tracks_daily["started_at"] <= signal_end)]
            df_tracks_daily.to_csv(os.path.join(save_dir,"tracks.csv"), index=False)

            LOGGER.info(f"Succesfully preprocessed {len(timestamps)} avro files and saved raw data in `{save_dir}` "+
                f"directory with {len(start_end_sessions)} music sessions")

            files_transfered = True

        elif already_transferred:
            LOGGER.info("Physiology and music session already transferred.")

        else:
            LOGGER.warning(f"Physiological data of {id_participant} with device {device_serial} and account {spotify_account} " + 
                    f"not synchronized with Empatica servers yet or participant did not wear the device today")

    return files_transfered

def session_physio_transfer(id_participant, spotify_account, pid, device_serial, participant_dir,
                             start_end_sessions, date, last_session_ts):
    """
    
    """

    n_transfered=0

    for music_session in start_end_sessions:
        LOGGER.info(start_end_sessions)
        session_id, started_at, ended_at = music_session.values()
        started_at_ts = int(datetime.fromisoformat(started_at).timestamp())
        ended_at_ts = int(datetime.fromisoformat(ended_at).timestamp())

        signals_session, timestamps, skipped = get_files_from_s3_ts_range(pid, device_serial, date, started_at_ts, ended_at_ts, last_session_ts, offset_minutes=60)

        if len(signals_session)>0:
            # Assign file name keeping original order
            # {start_ts_physio}_{end_ts_physio}_{session_id}
            save_dir = os.path.join(participant_dir, "_".join(map(str,[timestamps[0], timestamps[-1]]))+f"_{str(session_id).zfill(2)}")
            name_files = ["accelerometer.csv", "gyroscope.csv", "eda.csv", "temperature.csv",
                            "bvp.csv", "steps.csv", "tags.csv", "systolicPeaks.csv"]
            
            os.makedirs(save_dir, exist_ok=True)

            #
            for df_signal, file_name in zip(signals_session, name_files):
                file_path = os.path.join(save_dir, file_name)
                df_signal.to_csv(file_path, index=False)

            #
            tracks_obj = MusicListening.get_by_pid_session_id(pid, session_id)
            tracks_session = MusicListeningSchema(many=True, only=["listening_session_id", "track_session_id", "track_name","track_uri", "context",
                                                                    "device_type", "playback_inconsistency", "offline_playback" ,"started_at", "ended_at"]).dump(tracks_obj)["data"]
            df_tracks_session = pd.DataFrame.from_records(tracks_session)
            df_tracks_session["started_at"] = pd.to_datetime(df_tracks_session['started_at'], format='ISO8601').astype(int) // 10**3
            df_tracks_session['ended_at'] = pd.to_datetime(df_tracks_session['ended_at'], format='ISO8601').astype(int) // 10**3
            df_tracks_session.to_csv(os.path.join(save_dir,"tracks.csv"), index=False)

            
            LOGGER.info(f"Succesfully preprocessed {len(timestamps)} avro files and saved raw data in `{save_dir}` "+
                f"directory from session started at {started_at} and ended at {ended_at}")
            n_transfered+=1
        elif skipped: # ignore already downloaded data from previous sessions.
            continue
        else:
            LOGGER.warning(f"Physiological data of {id_participant} with device {device_serial} and account {spotify_account} " + 
                    f"not synchronized with Empatica servers yet or data was not captured during session {session_id}")
    return n_transfered

@with_appcontext
def transfer_physio_data(all_daily_physio):
    """
    
    """

    # today = datetime.today().strftime('%Y-%m-%d')
    # Running at 00:33, consider until yesterday
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    participant_obj = Participant.get_all_participants(is_active=True, is_withdrawn=False)
    active_participants = (ParticipantFlatSchema(many=True, only=["id", "pid", "spotify_account", "device_serial", "created_at"]).dump(participant_obj)).get("data")

    total_sessions_transfered = 0
    for participant in active_participants:
    
        # Check by active participants
        id_participant, pid, spotify_account, device_serial, created_at = participant.values()

        # Uniform naming convention to store participants data in independent directories 
        id_participant = f"P{str(id_participant).zfill(2)}"
        participant_dir = os.path.join(RAW_DIR, id_participant)


        if (device_serial is None ) or (spotify_account is None):
            continue
        
        # Get date of last session
        try:
            last_session_ts = int(sorted(os.listdir(participant_dir))[-1].split("_")[1])
            last_session_date = str(datetime.fromtimestamp(last_session_ts).date())
        except: # if no session exist, start from last modification date of participant resource
            last_session_date = str(datetime.fromisoformat(created_at).date())
            last_session_ts = int(datetime.fromisoformat(last_session_date).timestamp())

        # Check daily since last data transfer in case wristband did not syncrhonised data with the app
        date_range = list(pd.date_range(last_session_date, yesterday).strftime(date_format="%Y-%m-%d"))

        # Check daily activity
        LOGGER.info(f"Search and transfer physiological data from S3 to app for participant {pid} from {date_range[0]} to {date_range[-1]}")
        for date in date_range:
            
            start_session_obj = MusicListening.get_participant_daily_sessions_start(pid, date)
            end_session_obj = MusicListening.get_participant_daily_sessions_end(pid, date)

            start_sessions = MusicListeningSchema(many=True, only=["listening_session_id", "started_at"]).dump(start_session_obj)["data"]
            end_sessions = MusicListeningSchema(many=True, only=["listening_session_id", "ended_at"]).dump(end_session_obj)["data"]

            # Check sessions per day
            start_end_sessions = [{**start, **end} for start, end in zip(start_sessions, end_sessions)]
            if all_daily_physio:
                daily_transfered = daily_physio_transfer(id_participant, spotify_account, pid, device_serial, participant_dir, created_at,
                          start_end_sessions, date, last_session_ts)
                total_sessions_transfered+=daily_transfered
            else:
                LOGGER.debug("Downloading physiology aligned to music sessions")
                n_sessions_transfered = session_physio_transfer(id_participant, spotify_account, pid, device_serial, participant_dir,
                                                                start_end_sessions, date, last_session_ts)
                total_sessions_transfered+=n_sessions_transfered

    LOGGER.info(f"Number of sessions transfered: {total_sessions_transfered}")

    return

@with_appcontext
def notify_experiment_completion():
    """
    
    
    """

    today = datetime.today()

    days_experiment = timedelta(days=int(current_app.config.get("BATCH_PERIOD_DAYS", 21)))

    participant_obj = Participant.get_all_participants(is_active=True, is_completed=False, is_withdrawn=False)
    for obj in participant_obj:
        #
        if ((today - obj.created_at) >= days_experiment):
            participant_email = decrypt_email(obj.email_encrypted)
            greetings = f'Dear {obj.pid},'
            subject = f"BEATS Study - Arrange Meeting to Conclude Participation"
            thank_you = f"Congratulations, you have reached the end of the experimental period! Thank you for your meaningful contribution to our research."
            title = "Conclude Participation"
            next_steps = 'Please arrange a meeting to conclude the experiment and return the data collection instruments. Click the link below to schedule a convenient time.'
            button = "Schedule Meeting"
            link="https://calendly.com/2941451g-student/the-beats-dataset-study-completion-and-device-return"

            with mail.connect() as conn:
                msg = Message(subject=subject,
                            recipients=[participant_email],
                            html=render_template("email_template.html", 
                            title=title,
                            greetings=greetings,
                            thank_you=thank_you,
                            next_steps=next_steps,
                            button=button,
                            link=link))
                
                try:
                    conn.send(msg)
                    LOGGER.info(f"Participant {obj.pid} concluded data collection. Email to arranged a meeting and return device has been sent")
                    obj.is_completed = True
                    obj.save()
                except Exception:
                    LOGGER.exception(f"Unable to send email to {obj.pid} to conclude participation.")

    return


@click.command()
@click.option("--all_daily_physio", is_flag=True, show_default=True, default=False, help="If a music episode occurred, download all daily data. Otherwise just during music session.")
def run_daily_jobs(all_daily_physio):
    """
    Execute daily jobs
    """
    #
    daily_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "logs", f"daily_jobs.log")
    __setup_logger(daily_log_path)

    #
    try:
        purge_cache_and_not_verified()
    except Exception as e:
        LOGGER.error(f"An error occurred while conducting daily cleaning: {e}")

    #
    try:
        transfer_physio_data(all_daily_physio)
    except Exception as e:
        LOGGER.error(f"An error occurred while transfering physiological data to app: {e}")

    #
    try:
        notify_experiment_completion()
    except Exception as e:
        LOGGER.error(f"An error occurred while notifying experiment completion data to app: {e}")

        
