"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""
import spotipy
import os, sys, logging, click

import time
from datetime import datetime

import errno, fcntl

from app.routes.api.models.spotifyaccount import SpotifyAccount
from app.routes.api.models.participant import Participant
from app.routes.api.models.music import MusicListening
from app.utils import decrypt_email
from app.extensions import mail


from flask import current_app, render_template
from flask_mail import Message
from flask.cli import with_appcontext

#
LOGGER =logging.getLogger("scheduled_monitoring")

# Preselected playlist for study
STUDY_PLAYLISTS = {"spotify:playlist:37i9dQZF1DX3PFzdbtx1Us": "Cognitive",
                   "spotify:playlist:37i9dQZF1DX1s9knjP51Oa": "Affective",
                   "spotify:playlist:37i9dQZF1DWZqd5JICZI0u": "Eudaimonic",
                   "spotify:playlist:37i9dQZF1DX8NTLI2TtZa6": "Goal-Attainment"}



def __setup_logger(email_log, dir_path):
    """
    
    """

    global LOGGER

    #
    LOGGER.setLevel(logging.DEBUG)

    #
    path_file_handler = os.path.join(dir_path, "..", "..", "data", "logs", f"playback_{email_log}.log")
    file_handler = logging.FileHandler(path_file_handler)

    # Create formatters and add them to handlers
    formatter = logging.Formatter("[%(levelname)s] - [%(asctime)s.%(msecs)03d] - %(name)s - %(filename)s:%(lineno)s - %(funcName)s(): message: %(message)s",
                                   datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    #
    LOGGER.addHandler(file_handler)

    return


@with_appcontext
def __get_spotify_client(email):
    """
    """
    #
    scope = "user-read-playback-state user-read-email"

    #
    try:
        spotify_account = SpotifyAccount.get_by_email(email=email)
        if spotify_account is None:
            raise TypeError(f"Email `{email}` associated with Spotify account not in DB.")
    except:
        LOGGER.exception("Login first to monitor account playback state.")
        sys.exit (-1)
    
    try:
        spotify_cache_path = SpotifyAccount.get_by_email(email=email).cache_path
        cache_handler = spotipy.CacheFileHandler(cache_path=spotify_cache_path)
        auth = spotipy.SpotifyOAuth(client_id=current_app.config["SPOTIPY_CLIENT_ID"], client_secret=current_app.config["SPOTIPY_CLIENT_SECRET"],
                                    scope=scope, redirect_uri=current_app.config["SPOTIPY_REDIRECT_URI"], open_browser=False,
                                    cache_handler=cache_handler)
        spotify = spotipy.Spotify(auth_manager=auth)
        LOGGER.debug(f"Spotify Client Initialised with account {email}")
        
        return spotify
    except:
        LOGGER.exception(f"Unable to authenticate client for account `{email}`")
        sys.exit (-1)

@with_appcontext
def __validate_account_assignment(email):
    """
    
    """
    
    participant = Participant.get_by_linked_spotify(account_email=email)

    if participant is None:
        LOGGER.debug("No participant assigned to this account yet. Terminating programme.")
        sys.exit (-1)

    participant_pid = participant.pid
    participant_email = decrypt_email(participant.email_encrypted)
    
    return participant_pid, participant_email




def __get_playback_state(sp):
    """
    Use Spotipy to get playback state.
    TODO It may be more suitable to handle the error explained in main

    Input:
        sp(Spotipy): Spotipy client
    Output:
        current_state(dict/None): Response to current playback state of account
    """

    try:
        current_state = sp.current_playback()
        return current_state
    except:
        LOGGER.exception("Unable to get playback state")
        sys.exit (-1)


@with_appcontext
def __check_activity(sp, sleep_time, email, participant_pid):
    """
    
    """

    # Format milliseconds to minutes, seconds and remaining milliseconds for logger 
    # ms_to_min_sec = lambda ms: f"{ms // 60000}:{(ms % 60000 // 1000):02}"
    ms_to_min_sec = lambda ms: f"{ms // 60000}:{(ms % 60000 // 1000):02}.{(ms % 1000):03}"


    activity_detected = False

    # Check account playback state
    user_playback_state = __get_playback_state(sp)

    while user_playback_state is not None:

        # Extract only relevant information.
        # Plan workaround to handle instances when other type of 
        # content is listent using the provided account
        data = {
            "account_email":email,
            "participant_pid":participant_pid,
            "track_name": user_playback_state.get("item", dict()).get("name", None),
            "track_uri": user_playback_state.get("item", dict()).get("uri", None),
            "device_type": user_playback_state["device"]["type"],
            "device_id": user_playback_state["device"].get("id", None),
            "device_volume": user_playback_state["device"]["volume_percent"],
            "shuffle_state": user_playback_state["shuffle_state"],
            "smart_shuffle": user_playback_state["smart_shuffle"],
            "repeat_state": user_playback_state["repeat_state"],
            "last_playback_change": user_playback_state["timestamp"],
            "context_uri": user_playback_state.get("context", dict()).get("uri", None),
            "progress_track_ms": user_playback_state.get("progress_ms", None),
            "is_playing": user_playback_state["is_playing"],
            "created_at":datetime.fromtimestamp(time.time())

        }

        #
        music_listening = MusicListening(**data)
        music_listening.save()


        # Format message for logger
        log_msg = (
                    f"| Spotify Account: {email} | "
                    f"Participant pid: {participant_pid} | "
                    f"Song: {data['track_name']} | "
                    f"Context: {STUDY_PLAYLISTS.get(data['context_uri'], 'Other')} | "
                    f"Device: {data['device_type']} | "
                    f"Progress Track: {ms_to_min_sec(data['progress_track_ms'])} | "
                    f"Progress ms: {data['progress_track_ms']} | "
                    f"Last Playback Change: {datetime.fromtimestamp(user_playback_state['timestamp']/1000)} | " 
                    f"Currently Playing: {data['is_playing']} |"
                )
        
        LOGGER.info(log_msg)

        activity_detected = True

        time.sleep(sleep_time)
        user_playback_state = __get_playback_state(sp)

    return activity_detected

@with_appcontext
def __send_survey(participant_pid, account_email):
    """
    TODO replace account email with participant's email
      to which the Spotify account was assigned.
    """

    subject = 'BEATS Study - Please answer a quick survey!'
    title = "Music Activity Survey"
    greetings = 'Dear Participant,'
    thank_you = ''
    next_steps = 'We noticed you recently listened to some music. Please take a moment to answer a few questions about your experience by clicking the button below:'
    button = "Take the Survey"
    link = "https://uofg.qualtrics.com/jfe/form/SV_0HQk0nbMczLUpGm"

    with mail.connect() as conn:
        subject = subject
        msg = Message(subject=subject,
                      recipients=[account_email],
                      html=render_template("email_template.html", 
                      title=title,
                      greetings=greetings,
                      thank_you=thank_you,
                      next_steps=next_steps,
                      button=button,
                      link=link))

        try:
            conn.send(msg)
            LOGGER.info(f"Survey sent to participant {participant_pid}")
        except Exception:
            LOGGER.exception(f"Unable to send email to {participant_pid}")
            sys.exit (-1)



@click.command()
@click.argument('spotify_email', nargs=1)
@click.option('--sleep_time', default=30, help='Seconds to sleep between calls')
def monitor_playback_state(spotify_email,sleep_time):
    """
    Monitor playback state
    """

    #
    dir_path = os.path.dirname(os.path.abspath(__file__))
    lock_path = os.path.join(dir_path, "..", "..", "data", "locks", f".lock-{spotify_email}")

    #
    f = open (lock_path, 'w')
    try:
        fcntl.lockf (f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
        if e.errno == errno.EAGAIN:
            sys.stderr.write (f"{time.strftime('%d/%m/%Y %H:%M:%S')} - Script already running.\n")
            sys.exit (-1)

    #
    __setup_logger(spotify_email, dir_path)

    #
    spotify_client = __get_spotify_client(spotify_email)


    participant_pid, participant_email = __validate_account_assignment(spotify_email)

    #
    activity_detected = __check_activity(spotify_client, sleep_time, spotify_email, participant_pid)

    #
    if activity_detected:
        __send_survey(participant_pid, participant_email)
    else:
        LOGGER.debug("No activity detected")

    return
    