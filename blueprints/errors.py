from flask import Blueprint, render_template, abort, request, redirect, make_response
from helpers.auth import *
from helpers.db import *
from helpers.listings import paged_posts, SearchType, search_posts
from models.client import Client
from models.post import Post
from models.user import User, check_username, check_password
from models.permissions import Role, PunishmentType
from routes import routes

errors = Blueprint('errors', __name__, template_folder='../templates')

# confused monkey 404 not found error message
@errors.app_errorhandler(404)
def handle_404(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/404.html', user=local_user, routes=routes), 404

# gandalf 403 access forbidden error message
@errors.app_errorhandler(403)
def handle_403(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/403.html', user=local_user, routes=routes), 404

# can of spam 429 too many requests message
@errors.app_errorhandler(429)
def handle_429(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/429.html', user=local_user, routes=routes), 429

# epic explosion 500 server error message
@errors.app_errorhandler(500)
def handle_500(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/500.html', user=local_user, routes=routes), 500

# fake error for kicks and giggles
@errors.route("/error")
def fake_error():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/500.html', user=local_user, routes=routes), 500

# ban screen with expiration date (if applicable) and reason
@errors.route("/banned")
def banned_message():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    client = Client(connection, request.remote_addr)

    if local_user:
        if local_user.punishment_status == PunishmentType.BAN or local_user.punishment_status == PunishmentType.PERMABAN:
            return render_template('errors/user-banned.html', user=local_user, routes=routes)
    if client.punishment_status == PunishmentType.BAN:
        return render_template('errors/client-banned.html', user=local_user, client=client, routes=routes)
    return redirect("/")


