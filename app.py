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
from models.permissions import PunishmentType, Role
from werkzeug.middleware.proxy_fix import ProxyFix
from helpers.limiter import limiter

# Set up Flask app
app = Flask(__name__)

# Configures logging for the Flask server
# Code snippet from https://flask.palletsprojects.com/en/stable/logging/
# And also from https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
if not os.path.isdir('log'):
    os.makedirs('log')
dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
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
            'stream': 'ext://sys.stdout',
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
    'loggers': {
        'waitress': {
            'level': 'INFO',
            'handlers': ['wsgi'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'file']
    }
})

# set up logger for security
if os.getenv('PROXY_FIX') == 'true':
    with app.app_context():
        current_app.logger.info('Proxy fix is enabled')
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1) # thanks to https://sentry.io/answers/get-the-ip-address-of-a-visitor-in-flask/

load_dotenv()
limiter.init_app(app)

# not thanks to my good friend Tristin Porter for the rate limit system (it slowed down the website)
# https://github.com/nonsense-digital/IdiotNet/issues/1
@app.before_request
def before_request():
    # only track the client if it is requesting a non-static endpoint
    if request.endpoint != 'static' and request.endpoint != 'post.images':
        # get user, db, client info
        connection = get_db_connection()
        local_user, token = get_authenticated_user_and_token(connection, request.cookies)
        client = Client(connection, request.remote_addr)
        config = Config.get(connection)

        # don't do the ban message if the user is already on ban (we don't want an infinite loop)
        if request.endpoint != 'errors.banned_message' and request.endpoint != 'users.logout':
            # check for IP ban
            if client.check_punishment() == PunishmentType.BAN:
               return redirect("/banned")
            # check for user ban
            if local_user:
                if local_user.check_punishment() == PunishmentType.BAN or local_user.check_punishment() == PunishmentType.PERMABAN:
                    return redirect("/banned")
                # log out the user if they are unverified
                if local_user.role == Role.UNVERIFIED:
                    if config.require_email_verification:
                        token.delete()
                    else:
                        local_user.role = Role.MEMBER



        
# after-request housekeeping
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

# server shutdown cleanup
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

# before the server really does anything, make sure the database schema is correct
# an up-to-date schema will prevent weird database glitches from happening
with app.app_context():
    check_db_version()

# register blueprints
app.register_blueprint(main)
app.register_blueprint(users)
app.register_blueprint(posts)
app.register_blueprint(api)
app.register_blueprint(settings)
app.register_blueprint(admin)
app.register_blueprint(errors)