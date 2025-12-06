from flask import Blueprint, render_template, abort, request
from helpers.auth import *
from helpers.db import *
from helpers.listings import latest_posts
from routes import routes

main = Blueprint('index', __name__, template_folder='../templates')

# Main page, displaying a welcome message and some of the latest posts
@main.route(routes["home"])
def index():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('index.html', routes=routes, user=local_user, latest_posts=latest_posts)

# Simple description of the site and who made it
@main.route(routes["about"])
def about():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('about.html', routes=routes, user=local_user)