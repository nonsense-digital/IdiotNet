# a whole ton of imported modules
from __future__ import annotations
from flask import Flask, request, abort, redirect
from blueprints.posts import posts
from blueprints.settings import settings
from blueprints.users import users
from blueprints.API import api
from blueprints.admin import admin
from blueprints.errors import errors
from helpers.db import *
from helpers.auth import *
from models.auth_token import Token
import os
from dotenv import load_dotenv
from logging.config import dictConfig
from blueprints.main import main
from models.client import Client
from models.permissions import PunishmentType
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Set up Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1) # thanks to https://sentry.io/answers/get-the-ip-address-of-a-visitor-in-flask/
load_dotenv()

# thanks to https://flask-limiter.readthedocs.io/en/stable/
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per second"],
    storage_uri="memory://",
)

# Configures logging for the Flask server
# Code snippet from https://flask.palletsprojects.com/en/stable/logging/
# And also from https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
if not os.path.isdir('log'):
    os.makedirs('log')
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
        'plain': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'plain',
            'filename': './log/flask.log',
            'maxBytes': 51200
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'file']
    }
})

# thanks to my good friend Tristin Porter for the rate limit system
# https://github.com/nonsense-digital/IdiotNet/issues/1
requests_log = {}
temp_banned = []
@app.before_request
def before_request():
    # check if user is banned
    if request.endpoint and request.endpoint != 'static':
        connection = get_db_connection()
        local_user = get_authenticated_user(connection, request.cookies)
        client = Client(connection, request.remote_addr)
        if request.endpoint != 'errors.banned_message' and request.endpoint != 'users.logout':
            if client.check_punishment() == PunishmentType.BAN:
                return redirect("/banned")
            if local_user:
                if local_user.check_punishment() == PunishmentType.BAN or local_user.check_punishment() == PunishmentType.PERMABAN:
                    return redirect("/banned")

        

@app.after_request
def after_request(response):
    # if the delete token flag is present, delete the invalid token
    if hasattr(g, 'delete_token_cookie'):
        response.delete_cookie('token')
    elif 'token' in request.cookies:
        connection = get_db_connection()
        try:
            # extend lifetime of cookie
            token = Token.read(connection, request.cookies['token'])
            token.extend_lifetime(connection)
            response.set_cookie("token", request.cookies['token'], max_age=datetime.timedelta(days=7))
        except NameError:
            # delete cookie if invalid
            response.delete_cookie('token')
    return response

@app.teardown_appcontext
def teardown(exception):
    close_db_connection()

# thanks to https://stackoverflow.com/questions/79040845/flask-url-for-with-path-parameter-and-query-parameter#:~:text=1%20Answer,233
def combine_view_args(*args):
    dic = {}
    for arg in args:
        dic.update(arg)
    return dic
@app.context_processor
def utility_processor():
    return dict(combine_view_args=combine_view_args)

app.register_blueprint(main)
app.register_blueprint(users)
app.register_blueprint(posts)
app.register_blueprint(api)
app.register_blueprint(settings)
app.register_blueprint(admin)
app.register_blueprint(errors)