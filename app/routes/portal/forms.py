from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    institution = StringField('Institution', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ParticipantForm(FlaskForm):
    pid = StringField('Participant ID', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Register Participant')

class DeviceForm(FlaskForm):
    device_name = StringField('Device Name', validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[DataRequired()])
    measurement_location = StringField('Measurement Location', validators=[DataRequired()])
    submit = SubmitField('Register Device')


class AssociationForm(FlaskForm):
    participants = SelectField("Active Participants", choices=[])
    devices = SelectField("Available Devices", choices=[(None, "--")], default=None)
    spotify_accounts = SelectField("Available Spotify Acounts", choices=[(None, "--")], default=None)
    submit = SubmitField('Associate')

class WithdrawalForm(FlaskForm):
    participants = SelectField("All Participants", choices=[])
    submit = SubmitField('Withdraw')


    