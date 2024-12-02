"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""


from flask import Blueprint

# Blueprint for web routes
info_bp = Blueprint('info', __name__, template_folder='../../templates', static_folder='../../static')

# Import views to attach routes
from . import views