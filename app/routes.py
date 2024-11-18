"""
Routes for the application
------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from flask import Blueprint

main = Blueprint('main', __name__)

@main.route("/")
def hello_world():
    return "<p>Hello, World!</p>"