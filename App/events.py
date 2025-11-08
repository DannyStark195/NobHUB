from flask_socketio import SocketIO
from flask import request, session, current_app, flash
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, close_room, send
from .security import encrypt_message, decrypt_message
from .models import User, Messages, nob_db

from werkzeug.security import generate_password_hash, check_password_hash
socketio = SocketIO()
# active_users ={} 
chat_spaces = {}

@socketio.on("connect")
def handle_connect(data, auth=None):
    if current_user.is_authenticated:
        user_id = current_user.id
        username = current_user.username
        chat_space = session.get('chat_space')
        if not chat_space in chat_spaces:
            leave_room(chat_space)
            return
        join_room(chat_space)
        emit({'username': username, "message": "is online"}, to=chat_space)
        chat_spaces[chat_space]["users"]+=1
        chat_spaces[chat_space]["username"].append(username)
        print(f"{username} has joined chat space {chat_space}")
        print("User connected")
    return

@socketio.on('disconnect')
def handle_disconnect(sid=None):
    if current_user.is_authenticated:
        username= current_user.username
        chat_space = session.get('chat_space')
        leave_room(chat_space)
        if chat_space in chat_spaces:
            chat_spaces[chat_space]["users"]-=1
            chat_spaces[chat_space]["username"].remove(username)
            if chat_spaces[chat_space]["users"] <=0 :
                chat_spaces.pop(chat_space)
        send({'username': username, 'message': "is offline"}, to=chat_space)
        print(f"{username} has left chat space {chat_space}")
   

@socketio.on('send-message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return
    username = current_user.username
    chat_space = session.get('chat_space')
    user_message = data['data']
    print(user_message)

    user_message_hashed = encrypt_message(user_message)

    
    # contact_id = data.get('contact_id')
    # user_message = data.get('user_message')
    contact_id = session.get('contact_id')
    contact_name = session.get('contact_name')
    chat_messages = Messages(user_id=current_user.id, contact_id=contact_id, message=user_message_hashed)
    
    try:
        nob_db.session.add(chat_messages)

        nob_db.session.commit()
        chat_message = Messages.query.filter_by(user_id=current_user.id, contact_id=contact_id, message=user_message_hashed).first()
        print(chat_message.message)
        chat_message = Messages.query.filter_by(user_id=current_user.id, contact_id=contact_id, message=user_message_hashed).first()
        # timestamp = chat_message.time.strftime('%Y-%m-%d %H:%M')
        timestamp = chat_message.time.isoformat()+ 'Z'
        
        message_data={
            'user_id': current_user.id,
            'username': current_user.username,
            'contact_id': contact_id,
            'message': user_message,
            'time': timestamp
            }
        emit('send-message', message_data, to=chat_space)
        
        print(f"{username}: Message: {user_message}")
    except Exception as e:
        nob_db.session.rollback()
        print(e)
        return 
    
@socketio.on('typing')
def handle_typing(data):
    if not current_user.is_authenticated:
        return
    typer = data.get('typer')
    chat_space = data.get('chat_space')
    if chat_space:
        emit('typing', {'typer': typer, 'chat_space':chat_space}, room=chat_space, include_self=False)

@socketio.on('stopped typing')
def handle_stopped_typing(data):
    if not current_user.is_authenticated:
        return
    typer = data.get('typer')
    chat_space = data.get('chat_space')
    if chat_space:
        emit('typing', {'typer': typer, 'chat_space':chat_space}, room=chat_space, include_self=False)
    
    