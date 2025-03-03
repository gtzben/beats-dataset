"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

import os, bcrypt, hmac, hashlib, click, logging
from threading import Thread
from cryptography.fernet import Fernet

from itsdangerous import URLSafeTimedSerializer

from flask import current_app, render_template
from flask.cli import with_appcontext
from flask_mail import Message

from app.extensions import mail

from app.extensions import db
from app.routes.api.models.survey import Question, Questionnaire


def hash_password(password):
    """
    Hash password to store safely in DB. 
    Once password hashed, it can never be recovered
    --------------
    Inputs:
        password(str):
    
    Outputs:
        password_hashed(str):
    """
    password_hash = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt()).decode('utf-8')
    return password_hash

def hash_email(email):
    """Hashes an email deterministically using HMAC and a secret key."""
    return hmac.new(current_app.config["SECRET_KEY"].encode(), email.encode(), hashlib.sha256).hexdigest()


def check_password(password, hashed):
    """
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def encrypt_email(email):
    """
    
    """
    cipher_suite = Fernet(current_app.config["ENCRYPT_EMAIL_KEY"])
    string_encrypted = cipher_suite.encrypt(email.encode('utf-8')).decode('utf-8')
    return string_encrypted

def decrypt_email(encrypted_email):
    """
    
    """
    cipher_suite = Fernet(current_app.config["ENCRYPT_EMAIL_KEY"])
    string_decrypted = cipher_suite.decrypt(encrypted_email.encode('utf-8')).decode('utf-8')
    return string_decrypted


def generate_token(email, salt=None):
    """
    
    """
    serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY'))
    return serializer.dumps(email, salt=salt)


def verify_token(token, max_age=(60 * 60), salt=None):
    """
    
    """
    serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY'))
    try:
        email = serializer.loads(token, max_age=max_age, salt=salt)
    except:
        return False
    return email


def send_async_email(app, msg):
    with app.app_context():  # Push the app context
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.exception(f"Error while sending email asynchronously: {e}")


def send_email(to, subject, html, participant=None, **kwargs):
    """
    
    """

    try:
        app = current_app._get_current_object()  # Get the actual app instance
        msg = Message(subject,
                      recipients=[to],
                      html=render_template(html, **kwargs)
                      )

        Thread(target=send_async_email, args=(app, msg)).start()

        if participant:
            current_app.logger.info(f"Email '{subject}' sent to {participant}!")
        else:
            current_app.logger.info(f"Email '{subject}' sent to {to}!")

    except Exception as e:
        current_app.logger.exception(f"Error while sending the email '{subject}' to {to}: {e}")


def get_function_context(function_playlist_mapping, context_uri): 
    """
    Get music function of of playlists listened. If song is part of study, but 
    listened outside the context it won't count.
    -------
    Inputs:
        function_playlist_mapping(dict): Mapping music function and study playlists
        context_uri(str): 
    Output:
        func(str): Music function of passed playlist uri

    """   
    for func, playlists in function_playlist_mapping.items():
        if context_uri in playlists:
            return func
    return "Other"


def seed_data():
    """Insert seed data into the database"""

    surveys = [
        {'name': 'demo', 'description':'Demographics', 'n_items':30},
        {'name': 'tipi', 'description':'Ten-Item Personality Inventory', 'n_items':10},
        {'name': 'panas', 'description':'Positive and Negative Affect Schedule', 'n_items':20},
        {'name': 'pss', 'description':'Perceived Stress Scale', 'n_items':14},
        {'name': 'phq9', 'description':'Patient Health Questionnaire', 'n_items':9},
        {'name': 'stompr', 'description':'Short Test Of Music Preferences - Revised', 'n_items':23},
        {'name': 'gms', 'description':'The Goldsmiths Musical Sophistication Index', 'n_items':39}
    ]

    for survey_data in surveys:
        if not Questionnaire.query.filter_by(name=survey_data['name']).first():
            questionnaire = Questionnaire(**survey_data)
            questions = [Question(questionnaire_name=survey_data['name'], n_item=s+1) for s in range(survey_data['n_items'])]
            
            db.session.add(questionnaire)
            db.session.bulk_save_objects(questions)
    
    db.session.commit()
    print("Seed data inserted.")


@click.command()
@with_appcontext
def reset_db():
    """Resets the database and runs all migrations"""
    
    # Drop all tables (to reset)
    db.drop_all()
    print("Dropped all tables.")
    
    # Create all tables from the current models
    db.create_all()
    print("Created all tables.")
    
    # Seed the lookup tables
    seed_data()

    # Run migrations to apply changes (if any)
    from flask_migrate import upgrade
    upgrade()  # This applies any new migrations you might have
    print("Applied migrations.")


def setup_periodic_jobs_logger(path_file_handler, logger):
    """
    
    """


    #
    logger.setLevel(logging.DEBUG)

    #
    file_handler = logging.FileHandler(path_file_handler)

    # Create formatters and add them to handlers
    formatter = logging.Formatter("[%(levelname)s] - [%(asctime)s.%(msecs)03d] - %(name)s - %(filename)s:%(lineno)s - %(funcName)s(): message: %(message)s",
                                   datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    #
    logger.addHandler(file_handler)

    return logger


@with_appcontext
def send_error_email(logger, email_content):
    """

    """


    # Assign variables (optional, or use `default_values` directly)
    subject = email_content["subject"]
    title = email_content["title"]
    greetings = email_content["greetings"]
    first_sentence = email_content["first_sentence"]
    important_info = email_content["important_info"]
    button = email_content["button"]
    link = email_content["link"]

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
            logger.exception("Error email sent to experimenter")
        except Exception:
            logger.exception(f"Unable to send error email")
            raise


def handle_error_notification(error_details, error_file, logger):
    """
    Sends an email notification only once per issue using a flag file.
    """
    if not os.path.exists(error_file):

        # Default values
        default_values = {
            "subject": "BEATS Study - An Error Occured",
            "title": "Immediate Attention Required",
            "greetings": "Dear Experimenter,",
            "first_sentence": "An error has occurred while running a periodic job. The app may not be functioning correctly.",
            "important_info": f"Error Details: {error_details.get('error_message', 'Unknown Error')}",
            "button": "",
            "link": "",
        }

        # Merge provided details with defaults
        email_content = {**default_values, **error_details}
        send_error_email(logger, email_content)
        
        # Create file to avoid sending repeated emails
        with open(error_file, "w") as f:
            f.write(f"Error reported: {error_details.get('error_message', 'Unknown Error')}")