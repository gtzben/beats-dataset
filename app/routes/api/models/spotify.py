"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""

from app.extensions import db

class SpotifyAccount(db.Model):
    """
    TODO

    """
    __tablename__='spotifyaccounts'

    id = db.Column(db.Integer,primary_key=True)# Numeric id
    participant_id = db.Column(db.Integer,db.ForeignKey('participant.id'), default=None)
    email = db.Column(db.String(200), nullable=False, unique=True)
    uri = db.Column(db.String(50), nullable=False, unique=True)
    cache_path = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()


    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()