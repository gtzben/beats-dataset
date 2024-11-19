"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

import bcrypt

from itsdangerous import URLSafeTimedSerializer

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail


def hash_string(string):
    """
    """
    string_hashed = bcrypt.hashpw(string.encode('utf-8'),bcrypt.gensalt())
    return string_hashed.decode('utf-8')


def check_string(string, hashed):
    """
    """
    return bcrypt.checkpw(string.encode('utf-8'), hashed.encode('utf-8'))


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


def send_email(to, subject, link, html):
    """
    
    """

    try:
        msg = Message(subject,
                      recipients=[to],
                      html=render_template(html, link=link)
                      )
        
        mail.send(msg)

        current_app.logger.debug(f"Email '{subject}' sent to {to}!")

    except Exception as e:
        current_app.logger.exception(f"Error while sending the email '{subject}' to {to}")