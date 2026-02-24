from flask import Blueprint, render_template, abort, request, redirect, make_response

from helpers import mailer
from helpers.auth import *
from helpers.db import *
from helpers.limiter import limiter
from helpers.listings import paged_posts, SearchType, search_posts
from helpers.mailer import EmailType
from models.client import Client
from models.permissions import PunishmentType, Role
from models.post import Post
from models.user import User, check_username, check_password
from models.verify import Verify
from routes import routes

users = Blueprint('users', __name__, template_folder='../templates')

# a user's profile, consisting of username, followers, mod status, bio, latest posts, liked posts
# and also extra menus for your own profile and for admins
@users.route(routes["user"].format("<username>"))
def user(username):
    try:
        connection = get_db_connection()
        local_user = get_authenticated_user(connection, request.cookies)
        search_user = User.read(connection, username)
        posts_latest = search_posts(3, 0, search_user=search_user, search_type=SearchType.USER_POSTS)
        posts_liked = search_posts(3, 0, search_user=search_user, search_type=SearchType.USER_LIKED_POSTS)
        return render_template('users/user.html', routes=routes, posts_latest=posts_latest, posts_liked=posts_liked,
                               user=local_user, search_user=search_user)
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] User {username} not found.")
        abort(404, "User not found")

# a list displaying the latest posts of a specific user
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
        posts, is_last_page = paged_posts(page, search_user=search_user, search_type=SearchType.USER_POSTS)

        return render_template('users/posts.html', type="Posts", routes=routes, user=local_user, posts=posts,
                               is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] User {username} not found.")
        abort(404, "User not found")

# a list displaying the latest liked posts of a specific user
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
        posts, is_last_page = paged_posts(page, search_user=search_user, search_type=SearchType.USER_LIKED_POSTS)

        return render_template('users/posts.html', type="Liked Posts", routes=routes, user=local_user, posts=posts,
                               is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] User {username} not found.")
        abort(404, "User not found")

# login menu, using password hashing and auth tokens for secure authentication
@users.route(routes["login"], methods=['GET', 'POST'])
@limiter.limit('10 per minute')
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
                if check_password_hash(local_user.password_hash, password):
                    if local_user.role.level > 0:
                        current_app.logger.info(f"[IP {request.remote_addr}] User {username} logged in successfully.")
                        token = Token.create(connection, local_user.user_id, request.remote_addr)
                        resp = make_response(redirect(routes["home"]))

                        resp.set_cookie('token', token.token_id)
                        return resp
                    else:
                        verify = Verify.read(connection, user_id=local_user.user_id)
                        return render_template("settings/email/await_verify.html", routes=routes,
                                               verify=verify, first_time=True)
                else:
                    current_app.logger.warning(f"[IP {request.remote_addr}] User {username} failed to log in")
                    return render_template("users/login.html", routes=routes,
                                           error_message=f'Incorrect password')
            except NameError as e:
                current_app.logger.warning(f"[IP {request.remote_addr}] User {username} failed to log in")
                return render_template("users/login.html", routes=routes, user=local_user,
                                       error_message=f'User {username} does not exist')


# edit your bio on your profile
@users.route(routes["user_edit"].format("<username>"), methods=['GET', 'POST'])
def user_edit(username):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    client = Client(connection, request.remote_addr)

    if not local_user:

        return redirect(routes["login"])
    else:
        if request.method == 'GET':
            return render_template("users/edit.html", routes=routes, user=local_user, client=client)
        else:
            if local_user.punishment_status != PunishmentType.MUTE:
                content = request.form.get('content')
                local_user.bio = content
                current_app.logger.info(f"[IP {request.remote_addr}] {local_user.username} edited their user bio")
                return redirect(routes["user"].format(local_user.username))
            else:
                return render_template("users/edit.html", routes=routes, user=local_user, client=client)

# create your idiotnet account, using password hashing and auth tokens
@users.route(routes["signup"], methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def signup():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    config = Config.get(connection)

    if local_user:
        return redirect(routes["home"])
    else:
        if request.method == 'GET':

            return render_template("users/signup.html", routes=routes, user=local_user, error_message=None)
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            verify_password = request.form.get('verify_password')

            # disabled signup
            if not config.allow_signup:
                return render_template("users/signup.html", routes=routes, user=local_user, error_message=None)

            # join code check
            if config.join_code_required:
                if 'join_code' in request.form:
                    if request.form.get('join_code') != config.join_code:
                        return render_template("users/signup.html", routes=routes, user=local_user, error_message='Incorrect join code.')
                else:
                    return render_template("users/signup.html", routes=routes, user=local_user, form_data=request.form,)

            # email check
            email = ''
            if config.require_email:
                if request.form.get('email', '') == '':
                    return render_template("users/signup.html", routes=routes, user=local_user,
                                           form_data=request.form, error_message='Email required')

            # check for problems with username
            user_error = check_username(username)
            if user_error is not None:
                current_app.logger.warning(f"[IP {request.remote_addr}] Failed to create account: {user_error}")
                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message=user_error)

            # check for problems with password
            password_error = check_password(password, verify_password)
            if password_error is not None:
                current_app.logger.warning(f"[IP {request.remote_addr}] Failed to create account: {password_error}")
                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message=password_error)

            # make sure the user doesn't already exist
            try:
                test_user = User.read(connection, username)
                user_error = f'Username {test_user.username} already exists'
                current_app.logger.warning(f"[IP {request.remote_addr}] Failed to create account: {user_error}")
                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message=user_error)
            except NameError:
                # create the user!
                password_hash = hash_password(password) # hash the user's password

                final_email = None
                if config.require_email: # run this if email is included
                    email = request.form.get('email')
                    if config.require_email_verification: # send a verification email if needed
                        local_user = User.create(connection, username=username, password_hash=password_hash)
                        verify = Verify.create(connection, local_user.user_id, email)
                        mailer.send_email(local_user, EmailType.VERIFY_EMAIL, verify=verify)
                        return render_template("settings/email/await_verify.html", routes=routes,
                                               verify=verify, first_time=True)
                    else:
                        final_email = email # we are OK to include the email because no verification is needed


                local_user = User.create(connection, username=username, password_hash=password_hash, email=final_email) # create the user
                token = Token.create(connection, local_user.user_id, request.remote_addr) # create a token for the user

                resp = make_response(redirect(routes["home"]))
                resp.set_cookie('token', token.token_id) # add an auth token cookie so the browser remembers
                current_app.logger.info(f"[IP {request.remote_addr}] {username} created new account")
                return resp

# log out by deleting the auth cookie and removing the token from the database
@users.route(routes["logout"])
def logout():
    connection = get_db_connection()
    local_user, token = get_authenticated_user_and_token(connection, request.cookies)

    if not local_user:
        return redirect(routes["home"])
    else:
        token.delete()
        current_app.logger.info(
            f"[IP {request.remote_addr}] {local_user.username} logged out")
        return redirect(routes["home"])

# log out and then redirect to login page to switch accounts
@users.route(routes["switch"])
def switch():
    connection = get_db_connection()
    local_user, token = get_authenticated_user_and_token(connection, request.cookies)

    # log out if logged in
    if local_user:
        token.delete()
        current_app.logger.info(
            f"[IP {request.remote_addr}] {local_user.username} logged out")

    # redirect to log in
    return redirect(routes["login"])
