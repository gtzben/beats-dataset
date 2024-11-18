"""
This file initializes the Flask application
and handles any configurations.
------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from flask import Flask

def create_app():
    """
    
    """
    app = Flask(__name__)

     # Import and register blueprints (modular routes)
    with app.app_context():
        from .routes import main
        app.register_blueprint(main)

    return app