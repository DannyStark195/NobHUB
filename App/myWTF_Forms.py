from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_wtf.file import FileField, FileAllowed

class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username is required")])
    email = StringField("Email", validators=[DataRequired(message="Email is required"),Email(message="Enter a valid email address")])
    phoneNumber = StringField("Phone Number", validators=[Optional()])
    password0 = PasswordField("Password", validators=[DataRequired(message="Password is required"),  Length(min=8, message="Passwords must be greater than 8 digits")])
    password1 = PasswordField("Password", validators=[DataRequired(message="Password is required"),EqualTo('password0', message="Passwords must be same")])
    profile_pic = FileField("Profile",validators=[FileAllowed( ['jpg', 'jpeg', 'png','gif'], message='Please Upload an image!')])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):

    username = StringField("Username or Email", validators=[DataRequired(message="Username is required")])
    user_password = PasswordField("Password", validators=[DataRequired(message="Password is required")])
    submit = SubmitField("Login")

class EditForm(FlaskForm):
    username = StringField('Username', validators=[Optional()])
    email = StringField("Email", validators=[Optional(),Email(message="Enter a valid email")])
    phoneNumber = StringField('Phone Number', validators=[Optional()])
    about = StringField('About', validators=[Optional()])
    profile_pic = FileField("Profile", validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png','gif'], message='Please Upload an image')])
    edit = SubmitField("Edit")

class ResetPasswordForm(FlaskForm):
    password0 = PasswordField("Password", validators=[DataRequired(message="Password is required"),  Length(min=8, message="Passwords must be greater than 8 digits")])
    password1 = PasswordField("Password", validators=[DataRequired(message="Password is required"),EqualTo('password0', message="Passwords must be same")])
    reset = SubmitField('Reset Password')


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[Optional(), Email(message="Enter a valid email")])
    request = SubmitField("Request Reset")
    