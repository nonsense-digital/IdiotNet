# a whole ton of imported modules
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

# Set up Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1) # thanks to https://sentry.io/answers/get-the-ip-address-of-a-visitor-in-flask/

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
    # get login/db
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    client = Client(connection, request.remote_addr)

    # rate limit params
    ip = request.remote_addr
    now = datetime.datetime.now(datetime.UTC)
    window = 2      # seconds
    limit = 17       # max requests per window

    client.last_accessed = now

    # temporary IP ban message
    if ip in temp_banned and request.endpoint != 'static':
        current_app.logger.warning(f"[IP {request.remote_addr}] Cannot access the server due to a temporary IP ban.")
        abort(429, description="You have been temporarily banned.")

    # add ban if not in ban list already
    if ip not in requests_log:
        requests_log[ip] = []

    # keep only timestamps within the window
    requests_log[ip] = [t for t in requests_log[ip] if now - t < datetime.timedelta(seconds=window)]

    # 429 error for too many requests
    if len(requests_log[ip]) >= limit and request.endpoint != 'static':
        temp_banned.append(ip)
        current_app.logger.warning(f"[IP {request.remote_addr}] IP has been temporarily banned for spamming.")
        client.rate_limits += 1
        abort(429, description="Too Many Requests")
    requests_log[ip].append(now)

    # check if user is banned
    if request.endpoint and request.endpoint != 'errors.banned_message' and request.endpoint != 'static' and request.endpoint != 'static' and request.endpoint != 'users.logout':
        if client.check_punishment() == PunishmentType.BAN:
            print("Whar??")
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