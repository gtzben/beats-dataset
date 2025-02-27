"""
Simple main script to run application
------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
    # app.run()