"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""
import spotipy
import os, sys, logging, click

from requests.models import PreparedRequest

import time
from datetime import datetime, timedelta

import errno, fcntl

from app.routes.api.models.spotifyaccount import SpotifyAccount
from app.routes.api.models.participant import Participant
from app.routes.api.models.music import MusicListening
from app.utils import decrypt_email, get_function_context, setup_periodic_jobs_logger
from app.extensions import mail


from flask import current_app, render_template
from flask_mail import Message
from flask.cli import with_appcontext

from app.extensions import db

#
LOGGER =logging.getLogger("scheduled_monitoring")
ERROR_FLAG_FILE = "data/locks/.lock-email-error-playback-{date}"


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
        spotify = spotipy.Spotify(auth_manager=auth, retries=0, requests_timeout=10)
        # LOGGER.debug(f"Spotify Client Initialised with account {email}")
        
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

    participant_id = f"P{str(participant.id).zfill(2)}"
    participant_pid = participant.pid
    participant_email = decrypt_email(participant.email_encrypted)
    
    return participant_id, participant_pid, participant_email


def __get_playback_state(sp):
    """
    Use Spotipy to get playback state.
    TODO It may be more suitable to handle the error explained in main

    Input:
        sp(Spotipy): Spotipy client
    Output:
        current_state(dict/None): Response to current playback state of account
    """
    global ERROR_FLAG_FILE

    ERROR_FLAG_FILE = ERROR_FLAG_FILE.format(date=datetime.today().date())

    try:
        current_state = sp.current_playback()
        return current_state
    except spotipy.exceptions.SpotifyBaseException as e:
        LOGGER.error(f"Unable to get playback state: {e} - {e.headers}")

        # Send email only if not sent before
        if not os.path.exists(ERROR_FLAG_FILE):
            __send_error_email(f"Spotify API Error: {e}")
            with open(ERROR_FLAG_FILE, "w") as f:
                f.write(f"Error reported: {e}")

    except Exception as e:
        LOGGER.error(f"Unable to get playback state: {e}")

        # Send email only if not sent before
        if not os.path.exists(ERROR_FLAG_FILE):
            __send_error_email(f"Spotify API Error: {e}")
            with open(ERROR_FLAG_FILE, "w") as f:
                f.write(f"Error reported: {e}")
    
    sys.exit (-1)


@with_appcontext
def __check_activity(sp, sleep_time, email, participant_pid, tolerance=0.01, offline_limit=30):
    """
    
    """

    # Format milliseconds to minutes, seconds and remaining milliseconds for logger 
    ms_to_hh_mm_ss = lambda ms: f"{(ms // 3600000):02}:{(ms % 3600000 // 60000):02}:{(ms % 60000 // 1000):02}.{(ms % 1000):03}"

    # Check account playback state
    user_playback_state = __get_playback_state(sp)

    # Terminate if no activity
    if user_playback_state is None:
        # LOGGER.debug("No activity detected")
        sys.exit (-1)
        
    # Terminate if music is not being listened
    content_type = user_playback_state.get("currently_playing_type", None)
    if content_type != "track":
        LOGGER.debug(f"Participant {participant_pid} is listening `{content_type}` rather than music. Terminating programme.")
        sys.exit (-1)

    # Define some required variables for first iteration
    current_track_uri = user_playback_state.get("item", dict()).get("uri", None)
    started_at =  datetime.fromtimestamp(user_playback_state["timestamp"]/1000.0)
    ended_at = datetime.fromtimestamp(time.time()) 
    context_counter = {}
    playlists_in_context = {}
    n_session_tracks = 0
    track_ongoing = False
    record_id = None

    # Get session id if there are previous record. Otherwise, set as first session
    last_record = MusicListening.get_participant_last_record(participant_pid)


    if last_record:

        if user_playback_state.get("progress_ms", None) == last_record.progress_track_ms:
            LOGGER.warning("Activity detected due to lack of internet connection")
            sys.exit (-1)

        session_id = last_record.listening_session_id + 1
        
    else:
        session_id = 1
    #
    n_offline = 0
    while user_playback_state is not None:

        # Set times it not paused
        if user_playback_state["is_playing"]:
            started_at =  datetime.fromtimestamp(user_playback_state["timestamp"]/1000.0) # Last playback change (transition track)
            if n_session_tracks == 1:
                ended_at = datetime.fromtimestamp(time.time())  # if first track in session, set end to current time
            elif n_session_tracks>1:
                delta_progress = timedelta(milliseconds=int(user_playback_state.get("progress_ms", None) or 0))
                ended_at = datetime.fromtimestamp(user_playback_state["timestamp"]/1000.0) + delta_progress # add progress to started at

        # If track is ongoing, update. Otherwise create a new record.
        if track_ongoing:

            data = {
                "playback_inconsistency": True if datetime.fromtimestamp(user_playback_state["timestamp"]/1000.0) != music_listening.started_at else False,
                "offline_playback":True if n_offline!=0 else False,
                "device_volume": user_playback_state["device"]["volume_percent"],
                "shuffle_state": user_playback_state["shuffle_state"],
                "smart_shuffle": user_playback_state["smart_shuffle"],
                "repeat_state": user_playback_state["repeat_state"],
                "progress_track_ms": user_playback_state.get("progress_ms", None),
                # Cap elapsed time if issue with internet conection
                "elapsed_time_ms": int((ended_at - started_at).total_seconds() * 1000) if n_offline==0 else track_duration_ms,
                "last_playback_change_ms": user_playback_state["timestamp"],
                "monitored_at": datetime.fromtimestamp(time.time()),
                "ended_at": ended_at
            }

            music_listening = MusicListening.get_by_id(record_id=record_id)
            music_listening.update(data)

        else:
            
            # Get basic information of song played
            track_name = user_playback_state.get("item", dict()).get("name", None)
            track_duration_ms = user_playback_state.get('item', dict()).get('duration_ms', None)
            device_type = user_playback_state["device"]["type"]
            
            # Get context's uri if context exists, otherwise None
            current_context = user_playback_state.get("context", dict())
            context_uri = None if current_context is None else current_context.get("uri", None)
            
            # Check if context's uri is within the study contexts and count songs listened for each context
            context_cat = get_function_context(current_app.config['STUDY_PLAYLISTS'], context_uri)
            context_counter[context_cat]= context_counter.get(context_cat,0)+1

            # Keep track of playlists names within the context
            playlist_name = current_app.config['PLAYLISTS_URI_NAME'].get(context_uri, 'Non-Study Playlist')
            if (playlist_name == 'Non-Study Playlist') and any(current_track_uri in ss 
                                                             for ss in current_app.config['PROGRESS_TRACKING'].values()
                                                             if isinstance(ss,list)):
                playlist_name += " (Out-of-Context Study Song)" # Listened song belongs to study but was listened in another playlist

            playlists_in_context[context_cat] = playlists_in_context.get(context_cat, set()) | {playlist_name}
            
            n_session_tracks = sum(context_counter.values())
            

            data = {
                "participant_pid":participant_pid,
                "listening_session_id": session_id,
                "track_session_id": n_session_tracks,
                "account_email":email,
                "track_name": track_name,
                "track_uri": current_track_uri,
                "device_type": device_type,
                "device_id": user_playback_state["device"].get("id", None),
                "device_volume": user_playback_state["device"]["volume_percent"],
                "shuffle_state": user_playback_state["shuffle_state"],
                "smart_shuffle": user_playback_state["smart_shuffle"],
                "repeat_state": user_playback_state["repeat_state"],
                "context_uri": context_uri,
                # "context_cat": context_cat,
                "duration_ms": track_duration_ms,
                "progress_track_ms": user_playback_state.get("progress_ms", None),
                "elapsed_time_ms": int((ended_at - started_at).total_seconds() * 1000),
                "last_playback_change_ms": user_playback_state["timestamp"],
                "monitored_at": datetime.fromtimestamp(time.time()) ,
                "started_at": started_at,
                "ended_at": ended_at
            }
            
            music_listening = MusicListening(**data)
            music_listening.save()

        # Format message for logger
        log_msg = ( f"| ID track monitor: {music_listening.id} | "
                    f"Spotify Account: {email} | "
                    f"Participant pid: {participant_pid} | "
                    f"Session id: {session_id} | "
                    f"Track session id: {n_session_tracks} | "
                    f"Song: {track_name} | "
                    f"Context: {context_cat} | "
                    f"Study playlist: {playlist_name} | "
                    f"Device type: {device_type} | "
                    f"Track duration ms:  {track_duration_ms} | "
                    f"Progress track time: {ms_to_hh_mm_ss(user_playback_state.get('progress_ms', None))} | "
                    f"Progress ms: {user_playback_state.get('progress_ms', None)} | "
                    f"Progress %: {user_playback_state.get('progress_ms', None)/track_duration_ms:.2%} | "
                    f"Last playback change: {datetime.fromtimestamp(user_playback_state['timestamp']/1000)} | " 
                    f"Currently playing: {user_playback_state['is_playing']} | "
                    f"Offline Logging: {n_offline}/{offline_limit} |"

                )
        
        LOGGER.info(log_msg)

        # Sleep to avoid surpasing quota
        time.sleep(sleep_time)
        
        # Handle updating or creating new records
        user_playback_state = __get_playback_state(sp)
        if user_playback_state:
            if current_track_uri != user_playback_state.get("item", dict()).get("uri", None):
                current_track_uri = user_playback_state.get("item", dict()).get("uri", None)
                music_listening.ended_at = datetime.fromtimestamp(user_playback_state["timestamp"]/1000.0)
                music_listening.elapsed_time_ms = int((music_listening.ended_at - music_listening.started_at).total_seconds() * 1000)

                # Correct start time for fully listened to songs without playback inconsistencies
                if not music_listening.playback_inconsistency:
                    if 1-tolerance <= music_listening.elapsed_time_ms/music_listening.duration_ms <= 1+tolerance:
                        music_listening.started_at = music_listening.ended_at - timedelta(milliseconds=music_listening.duration_ms)
                    else:
                        music_listening.playback_inconsistency = True # The next button was pressed

                music_listening.save()
                track_ongoing = False
            else:
                track_ongoing = True
                record_id = music_listening.id
                if n_offline>=offline_limit:
                    LOGGER.warning("Potential internet connection issue since song has finished already")
                    break
                n_offline = n_offline+1 if user_playback_state.get('progress_ms', None)/track_duration_ms == 1 else 0

    #
    current_session = MusicListening.get_by_pid_session_id(participant_pid, session_id)
    session_total_ms = sum(record.elapsed_time_ms for record in current_session)

    #
    proportion_contexts = {context: count / n_session_tracks for context, count in context_counter.items()}
    dominant_context = max(proportion_contexts, key=proportion_contexts.get)

    # Get playlist name if only one playlist within the dominant context was listened
    if len(playlists_in_context[dominant_context]) == 1:
        playlist_listened = next(iter(playlists_in_context[dominant_context]))
    else:
        playlist_listened = ""


    LOGGER.info(f"Participant {participant_pid} listened to {n_session_tracks} songs lasting {ms_to_hh_mm_ss(session_total_ms)} in total for session {session_id}"+
                f", with the dominant context being {dominant_context + playlist_listened}")

    return session_id, n_session_tracks, session_total_ms, dominant_context, playlist_listened


@with_appcontext
def __send_survey(participant_id, participant_pid, session_id, account_email, dominant_context, playlist_listened):
    """
    TODO replace account email with participant's email
      to which the Spotify account was assigned.
    """

    subject = 'BEATS Study - Please answer a quick survey!'
    survey_type = "Music Activity Survey" if dominant_context=="Other" else f"{dominant_context + " " + playlist_listened} Survey"
    title = f"{survey_type} - Session {session_id}"
    greetings = f'Dear Participant {participant_pid},'
    first_sentence = ''
    next_steps = 'We noticed you recently listened to some music. Please take a moment to answer a few questions about your experience by clicking the button below:'
    button = "Take the Survey"

    req = PreparedRequest()
    params = {"ID":participant_id, "PID":participant_pid, "Sessions":session_id, "Functions": dominant_context,
              "Playlists":playlist_listened}
    req.prepare_url(current_app.config["SURVEY_LINK"], params)

    with mail.connect() as conn:
        subject = subject
        msg = Message(subject=subject,
                      recipients=[account_email],
                      html=render_template("email_template.html", 
                      title=title,
                      greetings=greetings,
                      first_sentence=first_sentence,
                      important_info="",
                      next_steps=next_steps,
                      button=button,
                      link=req.url,
                      show_link=False))

        try:
            conn.send(msg)
            LOGGER.info(f"{survey_type} sent to participant {participant_pid}")
        except Exception:
            LOGGER.exception(f"Unable to send email to {participant_pid}")
            sys.exit (-1)


@with_appcontext
def __send_error_email(error_message):
    """

    """

    subject = 'BEATS Study - Error Playback Monitoring Script '
    title = "Immediate Attention Required"
    greetings = f'Dear Experimenter,'
    first_sentence = 'An error has occurred while retrieving the playback state from Spotify. The app may not be functioning correctly.'
    important_info = f'Error Details: {error_message}'
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
                      important_info=important_info,
                      next_steps="",
                      button=button,
                      link=link,
                      show_link=False))

        try:
            conn.send(msg)
            LOGGER.info("Error email sent to experimenter")
        except Exception:
            LOGGER.exception(f"Unable to send error email")


@click.command()
@click.argument('spotify_email', nargs=1)
@click.option('--sleep_time', default=30, help='Seconds to sleep between calls')
@click.option('--th_songs', default=10, help='Number of songs to send survey')
@click.option('--th_minutes', default=30, help='Number of minutes to send survey')
@click.option("--send_email", is_flag=True, show_default=True, default=False, help="Send email survey after concluding a musical episode.")
def monitor_playback_state(spotify_email,sleep_time,send_email, th_songs, th_minutes):
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
    global LOGGER
    monitor_log_path = os.path.join(dir_path, "..", "..", "data", "logs", f"playback_{spotify_email}.log")
    LOGGER = setup_periodic_jobs_logger(monitor_log_path, LOGGER)


    #
    spotify_client = __get_spotify_client(spotify_email)


    participant_id, participant_pid, participant_email = __validate_account_assignment(spotify_email)

    #
    session_id, n_session_tracks, session_time_ms, dominant_context, playlist_listened = __check_activity(spotify_client, sleep_time, spotify_email, participant_pid)

    #
    if send_email and ((n_session_tracks>=th_songs) or (session_time_ms>= th_minutes * 6e4)):
        __send_survey(participant_id, participant_pid, session_id, participant_email, dominant_context, playlist_listened)
    else:
        LOGGER.info("Activity detected but survey not sent.")

    return
    