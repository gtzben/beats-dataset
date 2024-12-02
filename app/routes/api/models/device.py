"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""

from app.extensions import db

class Device(db.Model):
    __tablename__='device'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    device_name = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(50), nullable=False, unique=True)
    measurement_location = db.Column(db.String(50), nullable=False)
    is_assigned = db.Column(db.Boolean(), default=False) 
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    participant = db.relationship('Participant', backref='device')

    @classmethod
    def get_all_devices(cls, available_only=False):
        if available_only:
            return cls.query.filter_by(is_assigned=False).all()
        else:
            return cls.query.all()
        

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
        
    @classmethod
    def get_by_serial(cls, serial):
        return cls.query.filter_by(serial_number=serial).first()  

    @classmethod
    def get_all_by_participant_id(cls, participant_id):
        return cls.query.filter_by(participant_id=participant_id).first()
        
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

