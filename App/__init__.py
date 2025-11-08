from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail
from .events import socketio
from .models import nob_db, User
# from .routes import routes
# from .auth import auth
from .admin import admin
import secrets
import os

#The __init.py is like the settings and configuration of the flask app
#create a Flask instance in a function and call it in run.py to run the app
#Google OAUth login
oauth = OAuth()

mail = Mail()
def create_app():
    load_dotenv()
    secret_key0 = secrets.token_hex(16)
    secret_key1 = secrets.token_hex(16)
    app = Flask(__name__) #initialize the flask app instance
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nobdb.db' #configure database
    app.config['API_KEY'] = os.environ.get('API_KEY')  #configure gemini api-key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') #defines a secret key
    app.config['SYSTEM_INSTRUCTION_NOB'] = os.environ.get('SYSTEM_INSTRUCTION_NOB')
    app.config['SYSTEM_INSTRUCTION_DENNIS'] = os.environ.get('SYSTEM_INSTRUCTION_DENNIS')
    app.config['ENCRYPTION_KEY']= os.environ.get('ENCRYPTION_KEY')
    app.config['MAX_CONTENT_LENGTH'] = 10*1024*1024 #Sets the limit to how large a file can be to be uploaded(10MB)
    app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['.jpg', '.jpeg', '.png','.gif']
    app.config['PROFILE_IMAGE_PATH'] = 'User_profile_pics'
    app.config['CLIENT_ID'] = os.environ.get('CLIENT_ID')
    app.config['CLIENT_SECRET'] = os.environ.get('CLIENT_SECRET')
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
    mail.init_app(app)
    nob_db.init_app(app) #initializes the database
    # Reference site for authentication: https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login
    
    socketio.init_app(app)
    
    oauth.init_app(app) #Initialize oauth
    from .routes import routes

    app.register_blueprint(routes) #registers the routes from the route.py and the auth.py

    from .auth import auth

    app.register_blueprint(auth)
    app.register_blueprint(admin, url_prefix='/admin')
    
    from .auth import init_google_oauth
    init_google_oauth(app.config.get('CLIENT_ID'), app.config.get('CLIENT_SECRET'))
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        nob_db.create_all()
    
    return app