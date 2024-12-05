"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-12-04
"""

from app.extensions import db


class Questionnaire(db.Model):
    __tablename__ = 'questionnaire'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text)
    n_items = db.Column(db.Integer, nullable=False)

    questions = db.relationship('Question', backref='questionnaire')

    @classmethod
    def get_questions(cls, name):
        """Retrieve all questions for a given questionnaire name."""
        questionnaire = cls.query.filter_by(name=name).first()
        if not questionnaire:
            return []
        return questionnaire.questions


class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    questionnaire_name = db.Column(db.Integer, db.ForeignKey('questionnaire.name'), nullable=False)
    n_item = db.Column(db.Integer, nullable=False)

    responses = db.relationship('Response', backref='question')

    @classmethod
    def get_responses_for_participant(cls, participant_pid, questionnaire_name):
        """Retrieve all responses of a participant for a specific questionnaire."""
        return (
            db.session.query(Response)
            .join(Question, Response.question_id == Question.id)
            .filter(
                Question.questionnaire_name == questionnaire_name,
                Response.participant_pid == participant_pid,
            )
            .all()
        )


class Response(db.Model):
    __tablename__ = 'response'
    id = db.Column(db.Integer, primary_key=True)
    participant_pid = db.Column(db.String(50), db.ForeignKey('participant.pid'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    response = db.Column(db.Text, nullable=False)  # Adjust type for your response (e.g., Integer, String)
    created_at = db.Column(db.DateTime, default=db.func.now())

    @classmethod
    def bulk_insert(cls, responses_data):
        """Bulk insert responses."""
        responses = [cls(**data) for data in responses_data]
        db.session.bulk_save_objects(responses)
        db.session.commit()
  
