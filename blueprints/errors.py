from flask import Blueprint, render_template, abort, request, redirect, make_response
from helpers.auth import *
from helpers.db import *
from helpers.listings import paged_posts, SearchType, search_posts
from models.post import Post
from models.user import User, check_username, check_password
from models.permissions import Role, PunishmentType
from routes import routes

errors = Blueprint('errors', __name__, template_folder='../templates')

@errors.app_errorhandler(404)
def handle_404(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/404.html', user=local_user, routes=routes), 404

@errors.app_errorhandler(403)
def handle_403(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/403.html', user=local_user, routes=routes), 404

@errors.app_errorhandler(429)
def handle_429(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/429.html', user=local_user, routes=routes), 429

@errors.app_errorhandler(500)
def handle_500(e):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/500.html', user=local_user, routes=routes), 500

@errors.route("/error")
def fake_error():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('errors/500.html', user=local_user, routes=routes), 500

@errors.route("/banned")
def banned_message():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)

    expiration = local_user.punishment_expiration
    reason = local_user.punishment_reason

    if local_user.punishment_status == PunishmentType.BAN or local_user.punishment_status == PunishmentType.PERMABAN:
        return render_template('errors/banned.html', user=local_user, routes=routes)
    else:
        return redirect("/")


