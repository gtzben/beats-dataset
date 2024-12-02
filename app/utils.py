"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

import bcrypt, hmac, hashlib
from threading import Thread
from cryptography.fernet import Fernet

from itsdangerous import URLSafeTimedSerializer

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail


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
            current_app.logger.debug(f"Email '{subject}' sent to {participant}!")
        else:
            current_app.logger.debug(f"Email '{subject}' sent to {to}!")

    except Exception as e:
        current_app.logger.exception(f"Error while sending the email '{subject}' to {to}: {e}")