"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-20
"""
import time
from datetime import datetime
from app.extensions import db

class MusicListening(db.Model):
    """
    TODO

    """
    __tablename__='musiclistening'

    id = db.Column(db.Integer,primary_key=True)# Numeric id
    listening_session_id = db.Column(db.Integer, nullable=False)
    track_session_id= db.Column(db.Integer, nullable=False)
    participant_pid = db.Column(db.String(50), db.ForeignKey('participant.pid'), nullable=False) 
    account_email = db.Column(db.String(200), nullable=False)
    track_name = db.Column(db.String(200))
    track_uri = db.Column(db.String(50))
    device_type = db.Column(db.String(50))
    device_id = db.Column(db.String(50))
    device_volume = db.Column(db.Integer)
    shuffle_state = db.Column(db.Boolean())
    smart_shuffle = db.Column(db.Boolean())
    repeat_state = db.Column(db.String(10))
    context_uri = db.Column(db.String(50))
    playback_inconsistency = db.Column(db.Boolean(), default=False) # change to playback inconsistency (brief pause, scrub, restart, etc)
    duration_ms = db.Column(db.Integer) # Song time duration in milliseconds
    elapsed_time_ms = db.Column(db.Integer) # Total time elapsed from start to end in milliseconds. May include playback inconsistencies. 
    progress_track_ms = db.Column(db.Integer) # Monitor ongoing progress in milliseconds of current song.
    last_playback_change_ms = db.Column(db.Integer)
    monitored_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    ended_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    @classmethod
    def get_by_id(cls, record_id):
        return cls.query.filter_by(id=record_id).first()
    
    @classmethod
    def get_participant_last_record(cls, participant_pid):
        return (
        cls.query.filter_by(participant_pid=participant_pid)
        .order_by(cls.listening_session_id.desc())
        .first()
    )

    @classmethod
    def get_by_pid_session_id(cls, participant_pid, session_id):
        return (cls.query.filter_by(participant_pid=participant_pid,
                                    listening_session_id=session_id)
                                    .all())


    @classmethod
    def get_by_account_email(cls, email):
        return cls.query.filter_by(account_email=email).first()

    @classmethod
    def get_by_account_email(cls, email):
        return cls.query.filter_by(account_email=email).first()


    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, updates):
        for key, value in updates.items():
            if hasattr(self, key):  # Ensure the attribute exists on the model
                setattr(self, key, value)
            else:
                raise AttributeError(f"{key} is not a valid attribute of {self.__class__.__name__}")
        self.save()

    def delete(self):
        db.session.delete(self)
        db.session.commit()