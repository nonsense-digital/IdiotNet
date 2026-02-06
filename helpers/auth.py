import datetime
import bcrypt
from werkzeug.exceptions import BadRequestKeyError
from models.auth_token import Token
from models.user import User
from flask import g, current_app

# get a user object from an auth token cookie
def get_authenticated_user(connection, cookies):
    if 'token' in cookies:
        try:
            # test to see if the token is valid
            token_id = cookies['token']
            token = Token.read(connection, token_id)
            if datetime.datetime.now() >= token.valid_until:
                # mark for deletion if the token is expired
                g.delete_token_cookie = True
                return None
            try:
                # get the user object and return it
                user = User.read(connection, token.user_id)
                return user
            except NameError as error:
                # Mark for deletion if the corresponding user doesn't exist
                # I don't kno why this would happen, but it would mean something's seriously messed up here
                current_app.logger.error(f"Could not fetch auth user: {error}")
                g.delete_token_cookie = True
                return None
        except NameError as error:
            # Mark for deletion if the corresponding token doesn't exist
            g.delete_token_cookie = True
            return None
    else:
        # There is no token, so return null
        return None

# slightly different function, used if the authenticated user AND the token are needed (usually for logout)
def get_authenticated_user_and_token(connection, cookies):
    if 'token' in cookies:
        try:
            # test to see if the token is valid
            token_id = cookies['token']
            token = Token.read(connection, token_id)
            try:
                # get the user/token objects and return them
                user = User.read(connection, token.user_id)
                return (user, token)
            except NameError as error:
                # Mark for deletion if the corresponding user doesn't exist
                current_app.logger.error(f"Could not fetch auth user: {error}")
                g.delete_token_cookie = True
                return (None, None)
        except NameError as error:
            # Mark for deletion if the corresponding token doesn't exist
            current_app.logger.error(f"Could not fetch token: {error}")
            g.delete_token_cookie = True
            return (None, None)
    else:
        # There is no token, so return null
        return (None, None)

# hash and salt the password for security
# thanks to https://www.geeksforgeeks.org/python/hashing-passwords-in-python-with-bcrypt/
def hash_password(password: str|bytes|memoryview) -> bytes:
    if type(password) == bytes:
        password_bytes = password
    elif type(password) == memoryview:
        password_bytes = bytes(password)
    elif type(password) == str:
        password_bytes = password.encode('utf-8')
    else:
        raise TypeError('Password must be str, memoryview, or bytes')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    return password_hash

# hashes and salts the user-specified password to see if it matches the hashed password
# thanks to https://www.geeksforgeeks.org/python/hashing-passwords-in-python-with-bcrypt/
def check_password_hash(password_hash:str|bytes|memoryview, user_password: str) -> bool:
    if type(password_hash) == bytes:
        hash_bytes = password_hash
    elif type(password_hash) == memoryview:
        hash_bytes = bytes(password_hash)
    elif type(password_hash) == str:
        hash_bytes = password_hash.encode('utf-8')
    else:
        raise TypeError('Password Hash must be str, memoryview, or bytes')
    user_bytes = user_password.encode('utf-8')
    result = bcrypt.checkpw(user_bytes, hash_bytes)
    return result