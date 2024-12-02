from flask import render_template
from . import survey_bp

@survey_bp.route('/')
def main_page():
    """Render the main landing page."""
    return render_template('index.html')