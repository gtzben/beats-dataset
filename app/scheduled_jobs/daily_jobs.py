import os, click, logging
import pandas as pd
from datetime import datetime
from app.scheduled_jobs.connect_empatica_cloud import get_files_from_s3

from app.routes.api.models.user import User
from app.routes.api.models.participant import Participant
from app.routes.api.models.music import MusicListening
from app.routes.api.models.spotifyaccount import SpotifyAccount

from app.routes.api.schemas.participant import ParticipantFlatSchema
from app.routes.api.schemas.music import MusicListeningSchema

from app.routes.api.resources.spotify import cache_dir



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
            LOGGER.debug(f"User {user.email} was deleted from db since email verification expired")

    for participant in not_verified_participants:
        delta_days = (datetime.now()-participant.created_at).days
        if delta_days >= max_days_participants:
            participant.delete()
            LOGGER.debug(f"Participant {participant.pid} was deleted from db since email verification expired")
    
    removed_cache=0
    for cache in all_cache_spotify:
        if cache not in valid_cache_spotify:
            os.remove(cache)
            removed_cache+=1
    LOGGER.debug(f"Removed {removed_cache} cache files not linked to Spotify accounts in DB")


@with_appcontext
def transfer_physio_data():
    """
    
    """

    today = datetime.today().strftime('%Y-%m-%d')

    participant_obj = Participant.get_all_participants(is_active=True, is_verified=True)
    active_participants = (ParticipantFlatSchema(many=True, only=["id", "pid", "spotify_account", "device_serial", "updated_at"]).dump(participant_obj)).get("data")
    
    n_sessions_transfered = 0
    for participant in active_participants:
    
        # Check by active participants
        id_participant, pid, spotify_account, device_serial, updated_at = participant.values()

        if (device_serial is None ) or (spotify_account is None):
            continue

        participant_dir = os.path.join(RAW_DIR, pid)

        try:
            last_session_ts = int(sorted(os.listdir(participant_dir))[-1].split("_")[1])
            last_session_date = str(datetime.fromtimestamp(last_session_ts).date())
        except:
            last_session_date = str(datetime.fromisoformat(updated_at).date())
            last_session_ts = int(datetime.fromisoformat(last_session_date).timestamp())

        date_range = list(pd.date_range(last_session_date, today).strftime(date_format="%Y-%m-%d"))

        # Check daily activity
        LOGGER.info(f"Search and transfer physiological data from S3 to app for participant {pid} from {date_range[0]} to {date_range[-1]}")
        for date in date_range:
            
            start_session_obj = MusicListening.get_participant_daily_sessions_start(pid, date)
            end_session_obj = MusicListening.get_participant_daily_sessions_end(pid, date)

            start_sessions = MusicListeningSchema(many=True, only=["listening_session_id", "started_at"]).dump(start_session_obj)["data"]
            end_sessions = MusicListeningSchema(many=True, only=["listening_session_id", "ended_at"]).dump(end_session_obj)["data"]

            # Check sessions per day
            start_end_sessions = [{**start, **end} for start, end in zip(start_sessions, end_sessions)]
            for music_session in start_end_sessions:
                session_id, started_at, ended_at = music_session.values()
                started_at_ts = int(datetime.fromisoformat(started_at).timestamp())
                ended_at_ts = int(datetime.fromisoformat(ended_at).timestamp())

                signals_session, timestamps, skipped = get_files_from_s3(pid, device_serial, date, started_at_ts, ended_at_ts, last_session_ts)

                if len(signals_session)>0:
                    # Assign file name keeping original order
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
                    tracks_session = MusicListeningSchema(many=True, only=["track_session_id", "track_name","track_uri", "context",
                                                                           "playback_inconsistency", "offline_playback" ,"started_at", "ended_at"]).dump(tracks_obj)["data"]
                    df_tracks_session = pd.DataFrame.from_records(tracks_session)
                    df_tracks_session["started_at"] = pd.to_datetime(df_tracks_session['started_at'], format='ISO8601').astype(int) // 10**3
                    df_tracks_session['ended_at'] = pd.to_datetime(df_tracks_session['ended_at'], format='ISO8601').astype(int) // 10**3
                    df_tracks_session.to_csv(os.path.join(save_dir,"tracks.csv"), index=False)

                    
                    LOGGER.info(f"Succesfully preprocessed {len(timestamps)} avro files and saved raw data in `{save_dir}` "+
                        f"directory from session started at {started_at} and ended at {ended_at}")
                    n_sessions_transfered+=1
                elif skipped:
                    continue
                else:
                    LOGGER.warning(f"Physiological data of {pid} with device {device_serial} and account {spotify_account} " + 
                          f"not synchronized with Empatica servers yet or data was not captured during session {session_id}")

    LOGGER.info(f"Number of sessions transfered: {n_sessions_transfered}")


@click.command()
def run_daily_jobs():
    """
    Execute daily jobs
    """
    #
    daily_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "logs", f"daily_jobs.log")
    __setup_logger(daily_log_path)

    #
    purge_cache_and_not_verified()

    #
    try:
        transfer_physio_data()
    except Exception as e:
        LOGGER.error(f"An error occurred while transfering physiological data to app: {e}")

        
