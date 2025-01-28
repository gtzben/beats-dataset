"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""

from app.extensions import db

class Participant(db.Model):
    """
    TODO

    """
    __tablename__='participant'

    id = db.Column(db.Integer,primary_key=True)# Numeric id
    pid = db.Column(db.String(50), nullable=False, unique=True) # Pseudonym id
    email_hash = db.Column(db.String(200), nullable=False, unique=True) # Validate email since is deterministic but secure with key, cannot recover the original
    email_encrypted = db.Column(db.String(200), nullable=False, unique=True) # Can be decoded to send periodic emails
    ndh = db.Column(db.String(10), nullable=False)
    is_active = db.Column(db.Boolean(), default=False)
    is_verified = db.Column(db.Boolean(), default=False)
    is_withdrawn = db.Column(db.Boolean(), default=False)
    is_completed= db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    spotify_account = db.Column(db.String(200),db.ForeignKey('spotifyaccount.account_email'), nullable=True)
    device_serial = db.Column(db.String(200),db.ForeignKey('device.serial_number'), nullable=True, unique=False)

    musiclistening = db.relationship('MusicListening', backref='participant')



    @classmethod
    def get_all_participants(cls, is_active=None, is_verified=None, is_withdrawn=None, is_completed=None):
        query = cls.query

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        if is_verified is not None:
            query = query.filter_by(is_verified=is_verified)

        if is_withdrawn is not None:
            query = query.filter_by(is_withdrawn=is_withdrawn)

        if is_completed is not None:
            query = query.filter_by(is_completed=is_completed)

        return query.all()
        

    @classmethod
    def get_all_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()


    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
    
    @classmethod
    def get_by_pid(cls, pid):
        return cls.query.filter_by(pid=pid).first()
    
    @classmethod
    def get_by_linked_device(cls, serial_number):
        return cls.query.filter_by(device_serial=serial_number).first()
    
    @classmethod
    def get_by_linked_spotify(cls, account_email):
        return cls.query.filter_by(spotify_account=account_email).first()
    
    @classmethod
    def get_by_email_hash(cls,email_hash):
        return cls.query.filter_by(email_hash=email_hash).first()


    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    