from flask import request, render_template, abort
from flask.sansio.blueprints import Blueprint

from models.user import User
from routes import routes

users_bp = Blueprint('users', __name__)

@users_bp.route(routes["user"].format("<username>"))
def user(username):
    try:
        connection = get_db_connection()
        local_user = check_token(connection, request.cookies)
        search_user = User.read(connection, username)
        posts_latest = latest_posts(3, 0, search_user)
        posts_liked = latest_posts(3, 0, search_user, filter="liked")
        return render_template('users/user.html', routes=routes, posts_latest=posts_latest, posts_liked=posts_liked, user=local_user, search_user=search_user)
    except NameError:
        abort(404, "User not found")

@users_bp.route(routes["user_posts"].format("<username>"))
def user_posts(username):
    try:
        connection = get_db_connection()
        local_user = check_token(connection, request.cookies)
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        search_user = User.read(connection, username)
        posts, is_last_page = paged_posts(page, search_user)

        return render_template('users/posts.html', type="Posts", routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        abort(404, "User not found")

@users_bp.route(routes["user_liked_posts"].format("<username>"))
def user_liked_posts(username):
    try:
        connection = get_db_connection()
        local_user = check_token(connection, request.cookies)
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        search_user = User.read(connection, username)
        posts, is_last_page = paged_posts(page, search_user, filter="liked")

        return render_template('users/posts.html', type="Liked Posts", routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        abort(404, "User not found")