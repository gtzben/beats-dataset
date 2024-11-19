"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()