"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""


from flask import Blueprint

# Blueprint for web routes
survey_bp = Blueprint('info', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/survey')

# Import views to attach routes
from . import views