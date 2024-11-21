"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""

from app.extensions import db

class MusicListening(db.Model):
    """
    TODO

    """
    __tablename__='musiclistening'

    id = db.Column(db.Integer,primary_key=True)# Numeric id
    account_email = db.Column(db.String(200), nullable=False)
    participant_pid = db.Column(db.String(50), db.ForeignKey('participant.pid'), nullable=False) 
    track_name = db.Column(db.String(200))
    track_uri = db.Column(db.String(50))
    device_type = db.Column(db.String(50))
    device_id = db.Column(db.String(50))
    device_volume = db.Column(db.Integer)
    shuffle_state = db.Column(db.Boolean())
    smart_shuffle = db.Column(db.Boolean())
    repeat_state = db.Column(db.String(10))
    last_playback_change = db.Column(db.Integer)
    context_uri = db.Column(db.String(50))
    progress_track_ms = db.Column(db.Integer)
    is_playing = db.Column(db.Boolean())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())



    @classmethod
    def get_by_account_email(cls, email):
        return cls.query.filter_by(account_email=email).first()


    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()