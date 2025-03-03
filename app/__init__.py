"""
This file initializes the Flask application
and handles any configurations.
------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

import os, logging, datetime, spotipy, time, yaml
import pandas as pd

from flask import Flask, request
from flask_migrate import Migrate
from app.extensions import db, jwt, mail
from configparser import ConfigParser, ExtendedInterpolation
from app.scheduled_jobs.player_state_monitoring import monitor_playback_state
from app.scheduled_jobs.daily_jobs import run_daily_jobs
from app.scheduled_jobs.conditional_survey import run_survey_distribution


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
        if conf in ['sqlalchemy_database_uri', 'encrypt_email_key', 'jwt_access_token_expires',
                    'mail_port','mail_use_tls','mail_use_ssl']:
            app.config[conf.upper()] = eval(config[section][conf]) # requires os
        else:
            app.config[conf.upper()] = config[section][conf]

    # Load YAML study stimuli
    yaml_path = os.path.join("stimuli.yaml")    
    try:
        with open(yaml_path, "r") as file:
            function_playlists_tracks = yaml.safe_load(file)

        # Mapping function to playlists URIs
        app.config["STUDY_PLAYLISTS"] = {f: list(pt.keys()) for f, pt in function_playlists_tracks.items()}

        # Mapping playlists URIs to playlists names
        app.config["PLAYLISTS_URI_NAME"] = {p_uri:p_info["name"] for pt in function_playlists_tracks.values() for p_uri, p_info in pt.items()}
        
        # Mapping functions to track URIs
        app.config["PROGRESS_TRACKING"] = {f: [track for list_tracks in pt.values() for track in list_tracks["tracks"]] for f, pt in function_playlists_tracks.items()}
        app.config["PROGRESS_TRACKING"]["Participation Time"] = pd.Timedelta(days=int(app.config.get("BATCH_PERIOD_DAYS")))

    except Exception as e:
        app.config["STUDY_PLAYLISTS"] = {"Affective":[], "Eudaimonic":[], "Goal-Attainment":[]}
        app.config["PROGRESS_TRACKING"]  = {"Participation Time":pd.Timedelta(days=int(app.config.get("BATCH_PERIOD_DAYS"))),
                             "Affective":[], "Eudaimonic":[], "Goal-Attainment":[]}

        print(f"Error loading study playlists: {e}")


    # Register the blueprint
    app.register_blueprint(api_bp)
    app.register_blueprint(info_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(survey_bp)

    #
    __config_logger(app)
    __register_extensions(app)

    #
    app.cli.add_command(run_survey_distribution)
    app.cli.add_command(monitor_playback_state)
    app.cli.add_command(run_daily_jobs)
    app.cli.add_command(reset_db)

    # Seed data is required, if not in DB an error will occur
    # this may be the main reason for the analytics dashboard not
    # being available.
    try:
        create_dash_app(app)
        print("Analytics Dashboard Initialised Successfully")
    except:
        print("Dashboard not available. Check for errors or consider reseting the DB")

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