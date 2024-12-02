from flask import render_template
from . import info_bp

@info_bp.route('/')
def main_page():
    """Render the main landing page."""
    return render_template('index.html')