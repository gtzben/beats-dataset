"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-18
"""

from app.extensions import db

class User(db.Model):
    """
    TODO
    """
    __tablename__ = "user"

    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean(), default=False)
    is_superuser = db.Column(db.Boolean(),default=False)
    is_admin = db.Column(db.Boolean(),default=False)
    deleted = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    
    participants = db.relationship('Participant', backref='user')
    devices = db.relationship('Device', backref='user')

    @classmethod
    def get_by_id(cls, id, show_deleted=False):
        if show_deleted:
            return cls.query.filter_by(id=id).first()
        else:
            return cls.query.filter_by(id=id, deleted=show_deleted).first()

    @classmethod
    def get_by_email(cls,email, show_deleted=False):
        if show_deleted:
            return cls.query.filter_by(email=email).first()
        else:
            return cls.query.filter_by(email=email, deleted=show_deleted).first()
        
    @classmethod
    def get_all_users(cls, is_active=None, is_verified=None):
        query = cls.query

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        if is_verified is not None:
            query = query.filter_by(is_verified=is_verified)

        return query.all()

    @classmethod
    def get_not_verified(cls):
        return cls.query.filter_by(deleted=False, is_verified=False).all()
    
    @classmethod
    def get_all_verified_users(cls):
        return cls.query.filter_by(deleted=False, is_verified=True).all()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

