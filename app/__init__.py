"""
This file initializes the Flask application
and handles any configurations.
------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

import os, logging

from flask import Flask, request
from flask_migrate import Migrate
from app.extensions import db, jwt, mail
from app.scheduled_jobs.player_state_monitoring import monitor_playback_state
from configparser import ConfigParser, ExtendedInterpolation

from app.routes.api import api_bp
from app.routes.web import web_bp

from cryptography.fernet import Fernet

from app.routes.api.resources.token import black_list

def create_app(config_file="config.ini", section="DevelopmentConfig"):
    """
    
    """
    
    config  = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(config_file)

    app = Flask(__name__)

    #
    for conf in list(config[section]):
        if conf in ['sqlalchemy_database_uri', 'encrypt_email_key', 'study_playlists']:
            app.config[conf.upper()] = eval(config[section][conf]) # requires os
        else:
            app.config[conf.upper()] = config[section][conf]

    # Register the blueprint
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    #
    __config_logger(app)
    __register_extensions(app)

    #
    app.cli.add_command(monitor_playback_state)


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