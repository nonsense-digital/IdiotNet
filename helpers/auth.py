import datetime

from werkzeug.exceptions import BadRequestKeyError

from models.auth_token import Token
from models.user import User
from flask import g, current_app

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
                return user, token
            except NameError as error:
                # Mark for deletion if the corresponding user doesn't exist
                current_app.logger.error(f"Could not fetch auth user: {error}")
                g.delete_token_cookie = True
        except NameError as error:
            # Mark for deletion if the corresponding token doesn't exist
            current_app.logger.error(f"Could not fetch token: {error}")
            g.delete_token_cookie = True
    else:
        # There is no token, so return null
        return None