from flask import Blueprint, render_template, abort, request, redirect, make_response
from helpers.auth import *
from helpers.db import *
from helpers.listings import latest_posts, paged_posts
from models.post import Post, check_empty
from models.user import User, check_username, check_password
from routes import routes, API

users = Blueprint('users', __name__, template_folder='../templates')

@users.route(routes["user"].format("<username>"))
def user(username):
    try:
        connection = get_db_connection()
        local_user = get_authenticated_user(connection, request.cookies)
        search_user = User.read(connection, username)
        posts_latest = latest_posts(3, 0, search_user=search_user)
        posts_liked = latest_posts(3, 0, search_user=search_user, search_type="liked")
        return render_template('users/user.html', routes=routes, posts_latest=posts_latest, posts_liked=posts_liked, user=local_user, search_user=search_user)
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] User {username} not found.")
        abort(404, "User not found")

@users.route(routes["user_posts"].format("<username>"))
def user_posts(username):
    try:
        connection = get_db_connection()
        local_user = get_authenticated_user(connection, request.cookies)
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        search_user = User.read(connection, username)
        posts, is_last_page = paged_posts(page, search_user=search_user)

        return render_template('users/posts.html', type="Posts", routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] User {username} not found.")
        abort(404, "User not found")

@users.route(routes["user_liked_posts"].format("<username>"))
def user_liked_posts(username):
    try:
        connection = get_db_connection()
        local_user = get_authenticated_user(connection, request.cookies)
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        search_user = User.read(connection, username)
        posts, is_last_page = paged_posts(page, search_user=search_user, search_type="liked")

        return render_template('users/posts.html', type="Liked Posts", routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] User {username} not found.")
        abort(404, "User not found")





@users.route(routes["login"], methods=['GET', 'POST'])
def login():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)

    if local_user:
        return redirect(routes["home"])
    else:
        if request.method == 'GET':

            return render_template("users/login.html", routes=routes, user=local_user)
        else:
            username = request.form.get('username')
            password = request.form.get('password')

            try:
                local_user = User.read(connection, username)

                if local_user.password_hash == password:
                    current_app.logger.info(f"[IP {request.remote_addr}] User {username} logged in successfully.")
                    token = Token.create(connection, local_user.user_id)
                    resp = make_response(redirect(routes["home"]))


                    resp.set_cookie('token', token.token_id)
                    return resp
                else:
                    current_app.logger.warning(f"[IP {request.remote_addr}] User {username} failed to log in")
                    return render_template("users/login.html", routes=routes, user=local_user, error_message=f'Incorrect password')
            except NameError:
                current_app.logger.warning(f"[IP {request.remote_addr}] User {username} failed to log in")
                return render_template("users/login.html", routes=routes, user=local_user, error_message=f'User {username} does not exist')



@users.route(routes["user_edit"].format("<username>"), methods=['GET', 'POST'])
def user_edit(username):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)

    if not local_user:

        return redirect(routes["login"])
    else:
        if request.method == 'GET':

            return render_template("users/edit.html", routes=routes, user=local_user)
        else:
            content = request.form.get('content')

            local_user.bio = content
            current_app.logger.info(f"[IP {request.remote_addr}] {local_user.username} edited their user bio")
            return redirect(routes["user"].format(local_user.username))

@users.route(routes["signup"], methods=['GET', 'POST'])
def signup():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)

    if local_user:
        return redirect(routes["home"])
    else:
        if request.method == 'GET':

            return render_template("users/signup.html", routes=routes, user=local_user, error_message=None)
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            verify_password = request.form.get('verify_password')

            user_error = check_username(username)
            if user_error is not None:
                current_app.logger.warning(f"[IP {request.remote_addr}] Failed to create account: {user_error}")
                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message= user_error)

            password_error = check_password(password, verify_password)
            if password_error is not None:
                current_app.logger.warning(f"[IP {request.remote_addr}] Failed to create account: {password_error}")
                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message= password_error)

            try:
                test_user = User.read(connection, username)
                user_error = f'Username {test_user.username} already exists'
                current_app.logger.warning(f"[IP {request.remote_addr}] Failed to create account: {user_error}")
                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message=user_error)
            except NameError:
                local_user = User.create(connection, username=username, password=password)
                token = Token.create(connection, local_user.user_id)
                resp = make_response(redirect(routes["home"]))

                resp.set_cookie('token', token.token_id)
                current_app.logger.info(f"[IP {request.remote_addr}] {username} created new account")
                return resp

@users.route(routes["logout"])
def logout():
    connection = get_db_connection()
    local_user, token = get_authenticated_user_and_token(connection, request.cookies)

    if not local_user:
        return redirect(routes["home"])
    else:
        token.delete(connection)
        current_app.logger.info(
            f"[IP {request.remote_addr}] {local_user.username} logged out")
        return redirect(routes["home"])