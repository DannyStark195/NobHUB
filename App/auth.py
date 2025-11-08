from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory, session
from .models import nob_db
from .models import User, Contacts, Messages
from .NOB_AI import NOB
from .events import socketio
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from flask_mail import Message
from .myWTF_Forms import SignupForm, LoginForm, ResetPasswordForm, RequestResetForm
from . import oauth
from . import mail
import secrets
import os

#The auth.py defines the routes and logic for registration and authentication of users
auth = Blueprint('auth', __name__)
#Flask WTF

#Google OAUth login
# CLIENT_ID = current_app.config['CLIENT_ID']
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

def init_google_oauth(client_id, client_secret):
    """Initializes the Google OAuth client."""
    global google
    google = oauth.register(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={"scope":"openid profile email"}
    )

@auth.route('/signup', methods=['POST', 'GET'])
def signup():
    signup_form = SignupForm()
    if signup_form.validate_on_submit():

            user_password = signup_form.password0.data
            #Added and used flask wtf for form validation
            username= signup_form.username.data
            user_email= signup_form.email.data
            user_number= signup_form.phoneNumber.data
            
            user_profile_pic = signup_form.profile_pic.data
            if user_profile_pic:
                imagename= secure_filename(user_profile_pic.filename)
                user_image_path = os.path.join(current_app.config['PROFILE_IMAGE_PATH'], imagename)
                user_profile_pic.save(os.path.join('App/static',user_image_path))
            else:
                user_image_path= os.path.join(current_app.config['PROFILE_IMAGE_PATH'], 'defaultimg.jpg')
            user = User.query.filter_by(username=username).first()
            email = User.query.filter_by(user_email=user_email).first()

            if user:
                flash('Username already exist!')
                return redirect(url_for('auth.signup'))
            if email:
                flash('Email already registered!')
                return redirect(url_for('auth.signup'))

            user_password_hashed = generate_password_hash(user_password, method='pbkdf2:sha256')
            new_user = User(username=username, user_email=user_email, user_about="Hi I'm using Nobhub!", user_number=user_number,user_password_hash=user_password_hashed,user_image_path=user_image_path)
            
            
            try:
                nob_db.session.add(new_user)
                nob_ai_exists = User.query.filter_by(username='N.O.B').first()
                dennis_ai_exists = User.query.filter_by(username='Dennis').first()
                if not nob_ai_exists:
                    nob_ai = User(username='N.O.B', user_number='0000001', user_email='nob@ai.com', user_about="Hi I'm using Nobhub!", user_password_hash='-', user_image_path=os.path.join(current_app.config['PROFILE_IMAGE_PATH'], 'nobhublogosilverblue.png'))
                    nob_db.session.add(nob_ai)
                if not dennis_ai_exists:
                    dennis_ai = User(username='Dennis', user_number='0000002', user_email='dennis@ai.com', user_about="Hi I'm using Nobhub!", user_password_hash='-', user_image_path=os.path.join(current_app.config['PROFILE_IMAGE_PATH'], 'defaultimg.jpg'))
                    nob_db.session.add(dennis_ai)
                
            
                nob_db.session.commit()
                return redirect('/login')
            except Exception as e:
                nob_db.session.rollback()
                print(e)
                return "Error 101: Failed to add user. Please try again!"    
    
    return render_template('signup.html', signup_form=signup_form)


@auth.route('/login', methods=['GET','POST'])
def login():
   
    login_form = LoginForm()
    # username = None
    # user_password = None
    if login_form.validate_on_submit():
        username = login_form.username.data
        user_password = login_form.user_password.data
    
        user_or_email = User.query.filter(or_(User.username==username, User.user_email==username)).first()
        
        if not user_or_email:
            flash('Username or Email does not exist!')
            return redirect(url_for('auth.login'))

        if not user_or_email or not check_password_hash(user_or_email.user_password_hash, user_password):
            flash('Password is incorrect!')
            return redirect(url_for('auth.login'))
        login_user(user_or_email)
       
        
        return redirect(url_for('routes.home'))
    return render_template('login.html',login_form=login_form)
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

#Google login
@auth.route('/login/google')
def login_google():
    try: 
        redirect_url = url_for('auth.authorize_google', _external=True)
        print("YOO NO error")
        return google.authorize_redirect(
            redirect_url,
            prompt= 'select_account',
        )
        print("YOO error")
    except Exception as e:
        # This will now print the exact error message
        print(f"Error during login: {e}")
        flash('Sorry Failed to signin with google. Please try again')
        return redirect(url_for('auth.login'))
        # return "An error occurred. Check the server logs for details.", 500
# Authorize for google
@auth.route('/authorize/google')
def authorize_google():

    try:
        token = google.authorize_access_token()
        user_info_endpoint = google.server_metadata['userinfo_endpoint']
        resp = google.get(user_info_endpoint)
        user_info = resp.json()

        username_split = user_info['email'].split('@')
        username = '@'.join(username_split[:-1])
        print(username)
        user_email = user_info['email']
        print(user_email)
        user_or_email = User.query.filter_by(user_email=user_email).first()
        user_image_path= os.path.join(current_app.config['PROFILE_IMAGE_PATH'], 'defaultimg.jpg')
        if not user_or_email:
            new_user = User(username=username, user_email=user_email, user_number=f'{secrets.token_hex(16)}',user_password_hash=f'{secrets.token_hex(16)}',user_image_path=user_image_path, user_about="Hi I'm using Nobhub!")
                
            nob_db.session.add(new_user)
                    
            nob_db.session.commit()
        login_user(user_or_email)
                 
    except Exception as e:
                nob_db.session.rollback()
                print(e)
                flash('Sorry Failed to signup with google. Please try again')
                return redirect(url_for('auth.signup'))
    session['oauth_token'] = token
    login_user(user_or_email)
    return redirect(url_for('routes.home'))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('NobHUB: Reset Password Request', sender=current_app.config['MAIL_USERNAME'], recipients=[user.user_email])
    msg.body = f'''To reset your password, visit the following link: {url_for('auth.reset_password', token=token, _external=True)}
    If you did not make this request simply ignore this email and no changes would be made.
                '''
    mail.send(msg)
@auth.route('/reset_password', methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))
    reset_form = RequestResetForm()
    print("NO error")
    if reset_form.validate_on_submit():
        print("NO error")
        user = User.query.filter_by(user_email=reset_form.email.data).first()
        print(user)
        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password', 'info')
            return redirect(url_for('auth.login'))
    return render_template('request_reset.html', reset_form=reset_form)
@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Token is invalid or expired', 'warning')
        return redirect(url_for('auth.request_reset'))
    
    reset_form = ResetPasswordForm()
    if reset_form.validate_on_submit():
        user_password = reset_form.password0.data
        confirm_user_password = reset_form.password1.data
        print(user.user_email)
        user_password_hashed = generate_password_hash(user_password, method='pbkdf2:sha256')
        user.user_password_hash = user_password_hashed
        nob_db.session.commit()
        flash('Your password has been successfully Updated! You are now able to log in with new your password')
        return redirect(url_for('auth.login')) 
        
    return render_template('reset_password.html', reset_form=reset_form)