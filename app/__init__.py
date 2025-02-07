"""
This file initializes the Flask application
and handles any configurations.
------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

import os, logging, datetime, spotipy, time
import pandas as pd
from multiprocessing import Process, Manager

from flask import Flask, request
from flask_migrate import Migrate
from app.extensions import db, jwt, mail
from configparser import ConfigParser, ExtendedInterpolation
from app.scheduled_jobs.player_state_monitoring import monitor_playback_state
from app.scheduled_jobs.daily_jobs import run_daily_jobs

from app.utils import reset_db

from app.routes.api import api_bp
from app.routes.info import info_bp
from app.routes.portal import portal_bp
from app.routes.survey import survey_bp
from app.routes.analytics.dashboard import create_dash_app


from cryptography.fernet import Fernet

from app.routes.api.resources.token import black_list

def create_app(config_file="config.ini", section="DevelopmentConfig"):
    """
    
    """
    
    config  = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(config_file)

    app = Flask(__name__, static_url_path="/static")

    #
    for conf in list(config[section]):
        if conf in ['sqlalchemy_database_uri', 'encrypt_email_key', 'study_playlists', 'jwt_access_token_expires']:
            app.config[conf.upper()] = eval(config[section][conf]) # requires os
        else:
            app.config[conf.upper()] = config[section][conf]

    # Register the blueprint
    app.register_blueprint(api_bp)
    app.register_blueprint(info_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(survey_bp)

    #
    __config_logger(app)
    __register_extensions(app)

    #
    app.cli.add_command(monitor_playback_state)
    app.cli.add_command(run_daily_jobs)
    app.cli.add_command(reset_db)

    # Request Tracks URI. If quota has exceeded
    # or there is some issue with authorization 
    # causing the code to stop and preventing the app
    # from initialising, use a timeout to force the
    # app to start if takes longer than the expected.
    try:
        progress_tracking = __get_tracking_data_with_timeout(app, timeout=90)
        print("Progress tracking information loaded successfully")
    except Exception as e:
        print(f"Error while loading progress tracking, setting default instead: {e}")
        progress_tracking = {"Participation Time":pd.Timedelta(days=int(app.config.get("BATCH_PERIOD_DAYS"))),
                              "Affective":[], "Eudaimonic":[],"Goal-Attainment":[]}

    create_dash_app(app, progress_tracking)

    return app


class RequestFormatter(logging.Formatter):
    """
    
    """
    def format(self, record):
        record.url = request.url
        record.remote_addr = request.remote_addr
        record.method = request.method
        return super(RequestFormatter, self).format(record)
    

def __config_logger(app):
    """
    
    """

    app.logger.handlers.clear()

    api_formatter = RequestFormatter(
        '[%(asctime)s.%(msecs)03d] - %(remote_addr)s requested %(method)-4s %(url)s - %(levelname)s - [%(name)s - %(pathname)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler = logging.FileHandler("data/logs/app.log")

    file_handler.setLevel(logging.DEBUG) # set level accordingly
    file_handler.setFormatter(api_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG) # set level accordingly
    console_handler.setFormatter(api_formatter)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.propagate=False
    app.logger.setLevel(logging.DEBUG) # set level accordingly



def __register_extensions(app):
    """
    
    """

    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)


    mail.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, decrypted_token):

        """
        TODO
        """

        jti = decrypted_token['jti']
        return jti in black_list

    return

def __get_study_tracking_data(app, return_dict):
    """
    """

    # Playlist are public, thus no authorization is required.
    ccm = spotipy.SpotifyClientCredentials(client_id=app.config.get("SPOTIPY_CLIENT_ID"), client_secret=app.config.get("SPOTIPY_CLIENT_SECRET"))
    sp_ccm = spotipy.Spotify(client_credentials_manager=ccm, requests_timeout=5, retries=5)

    progress_tracking = {"Participation Time":pd.Timedelta(days=int(app.config.get("BATCH_PERIOD_DAYS"))), "Affective":[], "Eudaimonic":[],"Goal-Attainment":[]}
    n_uri_fetched = 0
    for func, pl_uris in app.config.get("STUDY_PLAYLISTS").items():
        for pl_id in pl_uris:
            offset = 0
            function_tracks = []
            while True:
                response = sp_ccm.playlist_items(pl_id,offset=offset,
                                            fields='items.track.id,total',
                                            additional_types=['track'])
                if len(response['items']) == 0:
                    break
                function_tracks.extend([f"spotify:track:{t['track']['id']}" for t in response['items']])
                offset += len(response['items'])
                n_uri_fetched+= len(response['items'])
                print(f"Track URIs fetched: {n_uri_fetched}")
                time.sleep(3) # Avoid too many request wait 3 seconds.
                
            progress_tracking[func].extend(function_tracks)

        print(f"Loaded URI tracks in {func} playlists")

    return_dict["data"] = progress_tracking

    return 

def __get_tracking_data_with_timeout(app, timeout=60):
    """Fetch playlist items but enforces a strict timeout."""
    with Manager() as manager:
        return_dict = manager.dict()  # Shared dictionary for results
        process = Process(target=__get_study_tracking_data, args=(app, return_dict))
    
        process.start()  # Start the process
        process.join(timeout)  # Wait for process to finish within timeout
        
        if process.is_alive():  
            process.terminate()  # Forcefully kill process if it exceeds timeout
            process.join()  
            raise Exception(f"Spotify API request timed out after {timeout} seconds.")
        
        return return_dict.get("data", None)  # Return fetched data if successful

