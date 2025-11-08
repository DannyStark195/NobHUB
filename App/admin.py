from flask import Blueprint, render_template, redirect, url_for, request, flash
from .models import nob_db
from .models import User, Contacts, Messages
from .NOB_AI import NOB
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required

#The auth.py defines the routes and logic for registration and authentication of users
admin = Blueprint('admin', __name__)

# admin_1 = User(username='admin1/DannyStark', user_number='1910107', user_email='dannystark195@')
@admin.route('/login')
def login():
    return render_template('adminlogin.html')

@admin.route('/login', methods=['POST'])
def login_post():
    admin_name = request.form.get('username')
    admin_password = request.form.get('password0')

    admin = User.query.filter_by(username=admin_name).first()
    if not admin:
        flash('admin does not exist!')

    if not admin or not check_password_hash(admin.user_password_hash, admin_password):
        flash('Password is incorrect!')
        return redirect(url_for('admin.login'))
    login_user(admin)
    return redirect('/home')
@admin.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))