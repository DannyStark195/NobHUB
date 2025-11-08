from flask import Blueprint, render_template, redirect, request, url_for, current_app, flash, session
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from .models import nob_db
from .models import User, Contacts, Messages
from .NOB_AI import NOB, Dennis, AIs
from .events import socketio, chat_spaces
from .myWTF_Forms import SignupForm, LoginForm, EditForm
from .security import encrypt_message, decrypt_message
import os
# The routes.py define the routes for the different pages 
routes = Blueprint('routes',__name__)
@routes.route('/')
def index():
    return render_template('index.html')
    
def contact_data(contacts):
    """
    Finds the latest message between two users (A->B or B->A).
    """
    no_messages = encrypt_message('No messages yet.')
    contacts_data = []
    for contact in contacts:
        # This calls the SQL query for *each* contact.
        user_contacts_entry = Contacts.query.filter_by(id=contact.id, user_id=current_user.id).first_or_404()  # get a table consisting of the contacts associated with a user from the Contacts table
        user_to_chatwith = User.query.get_or_404(user_contacts_entry.contact_id)
        last_message = Messages.query.filter(
        or_(
            and_(Messages.user_id == current_user.id, Messages.contact_id == user_to_chatwith.id),
            and_(Messages.user_id == user_to_chatwith.id, Messages.contact_id == current_user.id)
        )).order_by(Messages.time.desc()).first()
        # print(contact)
        # messages_filter =or_(
        #     and_(Messages.user_id == current_user.id, Messages.contact_id == user_to_chatwith.id),
        #     and_(Messages.user_id == user_to_chatwith.id, Messages.contact_id == current_user.id)
        # )
        # last_message = nob_db.session.execute(
        #     nob_db.select(Messages)
        #     .where(messages_filter)
        #     .order_by(Messages.time.desc()) # Sort from newest to oldest
        #     .limit(1)                             # Take only the newest one
        # ).scalar_one_or_none()
        print(last_message)
        
        # last_msg = contact_data(current_user.id, user_to_chatwith.id) 
            
        contacts_data.append({
                'id': contact.id,
                'contact_name': contact.contact_name,
                'contact_image_path': contact.contact_image_path,
                'last_message': last_message.message if last_message else no_messages, 
                
            })
        
    print(contacts_data)
    return contacts_data
    
@routes.route('/home', methods=["GET", "POST"])
@login_required
def home():
    contacts = Contacts.query.filter_by(user_id=current_user.id).all()
    
    contact_yourself_exists = Contacts.query.filter_by(user_id=current_user.id, contact_id=current_user.id).first()  #check if user's self exists as a contacts
    
    nob_ai = User.query.filter_by(username='N.O.B').first()   #get user N.O.B
    dennis_ai = User.query.filter_by(username='Dennis').first()  #get user Dennis
    contact_nob_exists = None
    if nob_ai:
        contact_nob_exists = Contacts.query.filter_by(user_id=current_user.id, contact_id=nob_ai.id).first() #check if N.O.B exists as a contacts
    contact_dennis_exists = None
    if dennis_ai:
        contact_dennis_exists = Contacts.query.filter_by(user_id=current_user.id, contact_id=dennis_ai.id).first() #check if Dennis exists as a contacts
    if not contact_yourself_exists or not contact_nob_exists or not contact_dennis_exists:
        try:
            if not contact_yourself_exists:
                contact_yourself= Contacts(user_id=current_user.id, contact_id=current_user.id, contact_name=current_user.username+' (Yourself)', contact_number=current_user.user_number, contact_image_path=current_user.user_image_path) #add user's self as a contact
                nob_db.session.add(contact_yourself)
            if nob_ai and not contact_nob_exists:
                contact_nob = Contacts(user_id=current_user.id, contact_id=nob_ai.id,contact_name=nob_ai.username, contact_number=nob_ai.user_number,contact_image_path=nob_ai.user_image_path)#add N.O.B as a contact
                nob_db.session.add(contact_nob)
            if dennis_ai and not contact_dennis_exists:
                contact_dennis = Contacts(user_id=current_user.id,contact_id=dennis_ai.id, contact_name=dennis_ai.username, contact_number=dennis_ai.user_number, contact_image_path=dennis_ai.user_image_path) #add Dennis as a contact
                nob_db.session.add(contact_dennis)
                     
            nob_db.session.commit()
            return redirect('/home')
        except Exception as e:
            nob_db.session.rollback() # go back to previous state before commit
            print(e)
            return "Error: 101"
    
    contacts = contact_data(contacts=contacts)
    decrypt_user_message = decrypt_message
    return render_template('home.html', contacts=contacts, user=current_user, decrypt_user_message=decrypt_user_message)
    
@routes.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@routes.route('/chat/<int:id>', methods=['GET', 'POST'])
@login_required
def chat(id):
    contacts = Contacts.query.filter_by(user_id=current_user.id).all()
    
    user_contacts_entry = Contacts.query.filter_by(id=id, user_id=current_user.id).first_or_404()  # get a table consisting of the contacts associated with a user from the Contacts table
    user_to_chatwith = User.query.get_or_404(user_contacts_entry.contact_id)                     #  get the contact/user to chat with from the users table
    messages = Messages.query.filter(
     or_(
         and_(Messages.user_id == current_user.id, Messages.contact_id == user_to_chatwith.id),
         and_(Messages.user_id == user_to_chatwith.id, Messages.contact_id == current_user.id)
     )).order_by(Messages.time).all()

    decrypt_user_message = decrypt_message
    

    # room setup (existing)
    chat_space = current_user.username+' | '+user_to_chatwith.username
    if user_to_chatwith.username+' | '+current_user.username in chat_spaces:
        chat_space = user_to_chatwith.username+' | '+current_user.username
    chat_spaces[chat_space] = {"users": 0, "username": []}

    session['chat_space'] = chat_space
    session['contact_id'] = user_to_chatwith.id
    session['contact_name'] = user_to_chatwith.username

    # read overlay flags from session (set by get_edit_message) and pop them so they don't persist
    dark_overlay = session.pop('dark_overlay', False)
    edit_overlay = session.pop('edit_overlay', False)
    edit_message_text = session.pop('edit_message_text', None)
    edit_message_id = session.pop('edit_message_id', None)

    delete_overlay = session.pop('delete_overlay', False)
    delete_message_id = session.pop('delete_message_id', None)

    contacts = contact_data(contacts=contacts)
    return render_template('chat.html',
                           contacts=contacts,
                           user=current_user,
                           messages=messages,
                           contact=user_contacts_entry,
                           user_to_chatwith=user_to_chatwith,
                           decrypt_user_message=decrypt_user_message,
                           AIs=AIs,
                           dark_overlay=dark_overlay,
                           edit_overlay=edit_overlay,
                           edit_message_text=edit_message_text,
                           edit_message_id=edit_message_id,
                           delete_overlay=delete_overlay,
                           delete_message_id=delete_message_id,
                           chat_space=chat_space)


@routes.route('/chat/AI/<int:id>', methods=['GET', 'POST'])
@login_required
def chat_AI(id):
    contacts = Contacts.query.filter_by(user_id=current_user.id).all()
    

    user_contacts_entry = Contacts.query.filter_by(id=id, user_id=current_user.id).first_or_404()  # get a table consisting of the contacts associated with a user from the Contacts table
    user_to_chatwith = User.query.get_or_404(user_contacts_entry.contact_id)                     #  get the contact/user to chat with from the users table
    messages = Messages.query.filter(
     or_(
         and_(Messages.user_id == current_user.id, Messages.contact_id == user_to_chatwith.id),
         and_(Messages.user_id == user_to_chatwith.id, Messages.contact_id == current_user.id)
     )).order_by(Messages.time).all()  
    ai_message = None
    decrypt_user_message = decrypt_message
    if request.method== 'POST':
        user_message=request.form.get('user_message')
        user_message_hashed = encrypt_message(user_message)
        chat_messages = Messages(user_id= current_user.id, contact_id=user_to_chatwith.id, message=user_message_hashed)
        
        if user_contacts_entry.contact_name== 'N.O.B':
            
            try:
                contact_nob_message = NOB(user_message)
                contact_nob_message_hashed = encrypt_message(contact_nob_message)
            except Exception as e:
                print('error', e)
                return redirect(url_for('routes.chat', id=id))
            ai_message = Messages(user_id= user_to_chatwith.id, contact_id=current_user.id, message=contact_nob_message_hashed)
            
        if user_contacts_entry.contact_name== 'Dennis':
            try:
                contact_dennis_message = Dennis(user_message)
                contact_dennis_message_hashed = encrypt_message(contact_dennis_message)
            except:
                return redirect(url_for('routes.chat', id=id))
            ai_message = Messages(user_id= user_to_chatwith.id, contact_id=current_user.id, message=contact_dennis_message_hashed)
           
        try:
            nob_db.session.add(chat_messages)
            if ai_message:
                nob_db.session.add(ai_message)
            nob_db.session.commit()
            print("success")

            return redirect(url_for('routes.chat_AI', id=id))

        except Exception as e:
            nob_db.session.rollback()
            print(e)
            return flash("Error 201: Failed to send message")
         
    # after commit / before render - same overlay pop logic as chat()
    dark_overlay = session.pop('dark_overlay', False)
    edit_overlay = session.pop('edit_overlay', False)
    edit_message_text = session.pop('edit_message_text', None)
    edit_message_id = session.pop('edit_message_id', None)

    delete_overlay = session.pop('delete_overlay', False)
    delete_message_id = session.pop('delete_message_id', None)

    contacts = contact_data(contacts=contacts)
    return render_template('chat.html',
                           contacts=contacts,
                           user=current_user,
                           messages=messages,
                           contact=user_contacts_entry,
                           user_to_chatwith=user_to_chatwith,
                           decrypt_user_message=decrypt_user_message,
                           AIs=AIs,
                           dark_overlay=dark_overlay,
                           edit_overlay=edit_overlay,
                           edit_message_text=edit_message_text,
                           edit_message_id=edit_message_id,
                           delete_overlay=delete_overlay,
                           delete_message_id=delete_message_id)


@routes.route('/search', methods=['GET'])
def search():
    users_to_find = request.args.get('search')
    print(users_to_find)
    users_found = User.query.filter(User.username.ilike(f"%{users_to_find}%")| User.user_number.ilike(f"%{users_to_find}%")).all()
    return render_template('users.html', users=users_found, users_to_find=users_to_find)

@routes.route('/add/<int:id>', methods=['GET', 'POST'])
@login_required
def add_contact(id):
    contact_found = User.query.get_or_404(id) # get a user if they exist
    contact = Contacts(user_id=current_user.id,contact_id=contact_found.id, contact_name=contact_found.username, contact_number=contact_found.user_number, contact_image_path=contact_found.user_image_path)
    reverse_contact = Contacts(user_id=contact_found.id, contact_id=current_user.id, contact_name=current_user.username, contact_number=current_user.user_number, contact_image_path=current_user.user_image_path)

    if contact_found.username == current_user.username:
        return redirect('/home')
    contact_exists = Contacts.query.filter_by(user_id=current_user.id, contact_name=contact_found.username).first()
    reverse_contact_exists = Contacts.query.filter_by(user_id=contact_found.id, contact_name=current_user.username).first()
    print(contact_exists)
    if contact_exists or reverse_contact_exists:
        return redirect('/home')
    
    try:
        nob_db.session.add(contact)
        nob_db.session.add(reverse_contact)
        nob_db.session.commit()
        print("successful")
        return redirect('/home')
    except Exception as e:
        print(e)
        return "Error 311: Failed to add contact"
    return redirect('/home')

@routes.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@routes.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    edit_form = EditForm()
    user_as_contact_everywhere = Contacts.query.filter_by(contact_id= current_user.id, contact_name=current_user.username)
    user_as_contact_yourself = Contacts.query.filter_by(user_id=current_user.id, contact_id=current_user.id).first()
    print(user_as_contact_everywhere)  
    print(user_as_contact_yourself)
    if edit_form.validate_on_submit():
       
        edited_username = edit_form.username.data
        edited_user_email = edit_form.email.data
        edited_user_number = edit_form.phoneNumber.data
        edited_user_about = edit_form.about.data
        user= User.query.filter_by(username=edited_username).first()
        email = User.query.filter_by(user_email=edited_user_email).first()
        if user:
                print("user:", user)
                flash('Username already exist! Please use another')
                return redirect(url_for('routes.edit_profile'))
        if email:
                flash('Email already registered! Please use another')
                return redirect(url_for('routes.edit_profile'))

        edited_profile_pic = edit_form.profile_pic.data
        if edited_profile_pic:
            imagename = secure_filename(edited_profile_pic.filename)
            image_path = os.path.join(current_app.config['PROFILE_IMAGE_PATH'], imagename)
            edited_profile_pic.save(os.path.join('App/static', image_path))
            current_user.user_image_path = image_path
            user_as_contact_everywhere.update({'contact_image_path':image_path }) 
            user_as_contact_yourself.contact_image_path = image_path
        if edited_username:
            current_user.username = edited_username
            user_as_contact_everywhere.update({'contact_name':edited_username }) 
            user_as_contact_yourself.contact_name = edited_username
        elif edited_user_email:
            current_user.user_email = edited_user_email
        elif edited_user_number:
            current_user.user_number = edited_user_number
            user_as_contact_everywhere.update({'contact_number': edited_user_number})
            user_as_contact_yourself.contact_number = edited_user_number
        elif edited_user_about:
            current_user.user_about = edited_user_about
            # user_as_contact_everywhere.update({'contact_number': edited_user_number})
        try:
            nob_db.session.commit()
            return redirect('/profile')
        except:
            nob_db.session.rollback()
            return redirect(url_for('routes.edit_profile'))

    
    return render_template('edit_profile.html', user=current_user, edit_form=edit_form)

@routes.route('/get/edit_message/<int:id>', methods=['GET'])
@login_required
def get_edit_message(id):
    # Find message, decrypt it, determine contact entry id, set session flags and redirect back to chat
    message_object = Messages.query.get_or_404(id)
    # decrypt message text for prefill
    try:
        message_to_edit = decrypt_message(message_object.message)
    except Exception:
        message_to_edit = ''  # fallback

    # determine the other user in this conversation
    if message_object.user_id == current_user.id:
        contact_id = message_object.contact_id
    else:
        contact_id = message_object.user_id

    # find the Contacts entry id for current_user <-> other_user
    contact_entry = Contacts.query.filter_by(user_id=current_user.id, contact_id=contact_id).first()
    if not contact_entry:
        # fallback: redirect to home if contact entry missing
        flash('Contact not found for editing.')
        return redirect(url_for('routes.home'))

    # set session flags so chat route will render overlay
    session['dark_overlay'] = True
    session['edit_overlay'] = True
    session['edit_message_text'] = message_to_edit
    session['edit_message_id'] = id

    return redirect(url_for('routes.chat', id=contact_entry.id))


@routes.route('/edit_message/<int:id>', methods=['POST'])
@login_required
def edit_message(id):
    # Update the message with the edited text and redirect back to the chat page
    message_to_edit = Messages.query.get_or_404(id)
    edited_message = request.form.get('edited_message') or request.form.get('user_message')
    contact_entry_id = request.form.get('contact_id')

    if not contact_entry_id:
        # attempt to derive contact entry id from the message object
        other_user = message_to_edit.contact_id if message_to_edit.user_id == current_user.id else message_to_edit.user_id
        contact_entry = Contacts.query.filter_by(user_id=current_user.id, contact_id=other_user).first()
        contact_entry_id = contact_entry.id if contact_entry else None

    if edited_message:
        try:
            new_encrypted = encrypt_message(edited_message)
            message_to_edit.message = new_encrypted
            nob_db.session.commit()
        except Exception as e:
            nob_db.session.rollback()
            flash('Could not save edited message.')
    # redirect back to the chat view (contacts id)
    if contact_entry_id:
        return redirect(url_for('routes.chat', id=int(contact_entry_id)))
    return redirect('/home')


@routes.route('/delete_message/<int:id>', methods=['POST'])
@login_required
def delete_message(id):
    # Delete and redirect back to the chat for the supplied contact_id
    contact_entry_id = request.form.get('contact_id')
    message_to_delete = Messages.query.get_or_404(id)
    try:
        nob_db.session.delete(message_to_delete)
        nob_db.session.commit()
    except Exception:
        nob_db.session.rollback()
        flash('Could not delete message.')

    if contact_entry_id:
        return redirect(url_for('routes.chat', id=int(contact_entry_id)))
    # fallback: try to derive contact_entry from message
    other_user = message_to_delete.contact_id if message_to_delete.user_id == current_user.id else message_to_delete.user_id
    contact_entry = Contacts.query.filter_by(user_id=current_user.id, contact_id=other_user).first()
    if contact_entry:
        return redirect(url_for('routes.chat', id=contact_entry.id))
    return redirect('/home')

@routes.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings.html')

@routes.route('/get/delete_message/<int:id>', methods=['GET'])
@login_required
def get_delete_message(id):
    # find message
    message = Messages.query.get_or_404(id)

    # determine other user 
    if message.user_id == current_user.id:
        contact_id = message.contact_id
    else:
        contact_id = message.user_id

    # find the contact entry id (Contacts table holds chat list entries)
    contact_entry = Contacts.query.filter_by(user_id=current_user.id, contact_id=contact_id).first()
    if not contact_entry:
        flash('Contact not found for deletion.')
        return redirect(url_for('routes.home'))

    # set session flags so chat() will render delete confirmation overlay
    session['dark_overlay'] = True
    session['delete_overlay'] = True
    session['delete_message_id'] = id

    return redirect(url_for('routes.chat', id=contact_entry.id))
# @routes.errorhandler(404)
# def page_not_found(e):
#     print("404")
#     return render_template('404.html'), 404