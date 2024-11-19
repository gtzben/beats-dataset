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
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    
    device = db.relationship('Device', backref='participant')

    @classmethod
    def get_all_participants(cls, only_active=False):
        if only_active:
            return cls.query.filter_by(is_active=only_active).all()
        else:
            return cls.query.all()
        

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
    def get_by_email_hash(cls,email_hash):
        return cls.query.filter_by(email_hash=email_hash).first()


    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    