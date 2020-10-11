import pyrebase

def create(auth, email, password, name, contact):
    return auth.create_user_with_email_and_password(email, password)

def user_login(auth, email, password):
    return auth.sign_in_with_email_and_password(email, password)

def verification(auth, email, password):
    user = auth.sign_in_with_email_and_password(email, password)
    auth.send_email_verification(user['idToken'])

def reset(auth, email):
    auth.send_password_reset_email(email)