from flask import current_app
from cryptography.fernet import Fernet

#The security.py defines the logic for encrypting and decrypting chat messages

def encrypt_message(message):
    key =  current_app.config['ENCRYPTION_KEY']
    fernet = Fernet(key)

    encoded_message = message.encode()
    encrypted_messge = fernet.encrypt(encoded_message)
    return encrypted_messge

def decrypt_message(message):
    key =  current_app.config['ENCRYPTION_KEY']
    fernet = Fernet(key)

    decrypted_message = fernet.decrypt(message)
    return decrypted_message.decode()