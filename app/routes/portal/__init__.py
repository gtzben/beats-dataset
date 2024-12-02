"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""


from flask import Blueprint, url_for, current_app


# Blueprint for web routes
portal_bp = Blueprint('portal', __name__, template_folder='../../templates', url_prefix='/portal')

# Import views to attach routess
from . import views