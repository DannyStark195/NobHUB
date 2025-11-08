from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin #UserMixin will add Flask-Login attributes to the model so that Flask-Login will be able to work with it.
from itsdangerous import  URLSafeTimedSerializer as Serializer
from datetime import datetime

# The models.py define the structure of the database. 
# The Users class defines the users table for all users
# The Contacts class defines the contacts table for all and each user's contact
# The Messages class defines the messages table for all each user and their contacts
# Reference site for authentication: https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login

nob_db = SQLAlchemy()

class User(UserMixin, nob_db.Model):
    id = nob_db.Column(nob_db.Integer, primary_key=True)
    username = nob_db.Column(nob_db.String(20), nullable=False)
    user_number = nob_db.Column(nob_db.String(200), nullable=True)
    user_email = nob_db.Column(nob_db.String(100), nullable=False)
    user_about = nob_db.Column(nob_db.String(200), nullable=False)
    user_password_hash = nob_db.Column(nob_db.String(200), nullable=False)
    user_image_path =  nob_db.Column(nob_db.String(200), nullable=False)
    user_contacts = nob_db.relationship('Contacts', backref='owner_user', lazy=True, primaryjoin="User.id==Contacts.user_id", overlaps="actual_contact_user") # A two way relationship between the user and their contacts and messages
    user_messages_sent = nob_db.relationship('Messages', backref='sender_user', lazy=True, primaryjoin="User.id==Messages.user_id", overlaps="user_messages_received")
    user_messages_received = nob_db.relationship('Messages',backref='recipient_user',lazy=True,primaryjoin="User.id == Messages.contact_id", overlaps="user_messages_sent")

    def get_reset_token(self, expires_sec=600):
        print(f"Secret Key: {current_app.config['SECRET_KEY']} | Type: {type(current_app.config['SECRET_KEY'])}")
    
        s = Serializer(str(current_app.config['SECRET_KEY']))
        
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_token(token, expires_sec=600):
        s = Serializer(str(current_app.config['SECRET_KEY']))
        try:
            user_id = s.loads(token, max_age=expires_sec)
        except:
            return None
        return User.query.get(user_id['user_id'])

class Contacts(nob_db.Model):
    id = nob_db.Column(nob_db.Integer, primary_key=True)
    user_id = nob_db.Column(nob_db.Integer, nob_db.ForeignKey('user.id'), nullable=False)
    contact_id = nob_db.Column(nob_db.Integer, nob_db.ForeignKey('user.id'), nullable=False)  
    contact_name = nob_db.Column(nob_db.String(20), nullable=False)
    contact_number = nob_db.Column(nob_db.String(200), nullable=True)
    contact_image_path =  nob_db.Column(nob_db.String(200), nullable=False)
    actual_contact_user = nob_db.relationship('User', primaryjoin="Contacts.contact_id==User.id", lazy=True, overlaps= "user_contacts, user_messages_sent, user_messages_received")

class Messages(nob_db.Model):
    id = nob_db.Column(nob_db.Integer, primary_key=True)
    user_id = nob_db.Column(nob_db.Integer, nob_db.ForeignKey('user.id'), nullable=False)
    contact_id = nob_db.Column(nob_db.Integer, nob_db.ForeignKey('user.id'), nullable=False)
    message = nob_db.Column(nob_db.Text, nullable=False)
    time = nob_db.Column(nob_db.DateTime, default=datetime.utcnow)

