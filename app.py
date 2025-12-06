# a whole ton of imported modules
import datetime
from flask import Flask, request, render_template, redirect, make_response, abort, jsonify, current_app

from blueprints.posts import posts
from blueprints.settings import settings
from blueprints.users import users
from blueprints.API import api
from models.comment import Comment
from models.post import Post, SortMethod, check_empty
from helpers.listings import *
from models.user import User, check_username, check_password
from helpers.db import *
from helpers.auth import *
from routes import routes, API
from models.auth_token import Token
import os
from dotenv import load_dotenv
from logging.config import dictConfig
from blueprints.main import main

# Set up Flask app
app = Flask(__name__)
load_dotenv()

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
def limit_requests():
    ip = request.remote_addr
    now = datetime.datetime.now(datetime.UTC)
    window = 1      # seconds
    limit = 25       # max requests per window

    if ip in temp_banned:
        current_app.logger.warning(f"[IP {request.remote_addr}] Cannot access the server due to a temporary IP ban.")
        abort(403, description="You have been temporarily banned.")

    if ip not in requests_log:
        requests_log[ip] = []

    # keep only timestamps within the window
    requests_log[ip] = [t for t in requests_log[ip] if now - t < datetime.timedelta(seconds=window)]

    if len(requests_log[ip]) >= limit:
        temp_banned.append(ip)
        current_app.logger.warning(f"[IP {request.remote_addr}] IP has been temporarily banned for spamming.")
        abort(429, description="Too Many Requests")

    requests_log[ip].append(now)

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

app.register_blueprint(main)
app.register_blueprint(users)
app.register_blueprint(posts)
app.register_blueprint(api)
app.register_blueprint(settings)