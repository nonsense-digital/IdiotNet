from werkzeug.exceptions import BadRequestKeyError

from models.auth_token import Token
from models.user import User
from flask import g, current_app

def get_authenticated_user(connection, cookies):
    if 'token' in cookies:
        try:
            token_id = cookies['token']
            token = Token.read(connection, token_id)
            try:
                user = User.read(connection, token.user_id)
                return user
            except NameError as error:
                current_app.logger.error(f"Could not fetch auth user: {error}")
        except NameError as error:
            current_app.logger.error(f"Could not fetch token: {error}")
    else:
        return None

