"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""


from flask import Blueprint

# Blueprint for web routes
survey_bp = Blueprint('survey', __name__, template_folder='../../templates', url_prefix='/survey')

# Import views to attach routes
from . import views