from flask import Blueprint, render_template, abort, request, redirect, make_response
from helpers.auth import *
from helpers.db import *
from helpers.listings import paged_posts, SearchType, search_posts, paged_clients, search_users, search_clients, \
    paged_users, paged_sessions
from models.client import Client
from models.comment import Comment
from models.config import Config
from models.post import Post
from models.user import User, check_username, check_password
from models.permissions import Role, PunishmentType
from routes import routes

# register blueprint
admin = Blueprint('admin', __name__, template_folder='../templates')

# function that checks if a user has the required permissions
# if not, abort with a 403 denied error
def check_admin(local_user:User, admin_only=False):
    match local_user.role:
        case Role.ADMIN:
            return
        case Role.MODERATOR:
            if admin_only:
                abort(403)
        case Role.MEMBER:
            abort(403)
        case _:
            abort(403)

# main admin dashboard - this is where you can see all users and server settings
@admin.route(routes["admin_dashboard"])
def dashboard():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    users = search_users(10, search_type=SearchType.ALL)
    clients = search_clients(10, search_type=SearchType.ALL)
    config = Config(connection)
    return render_template("admin/index.html", user=local_user, routes=routes, users=users, clients=clients, config=config)

# configuration menu for join code, post approval, etc
@admin.route(routes["admin_config"], methods=["GET", "POST"])
def config():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user, True)
    config = Config(connection)
    if request.method == "GET":
        return render_template("admin/config.html", routes=routes, user=local_user, config=config)
    else:
        if 'require_join_code' in request.form:
            if 'join_code' in request.form:
                config.join_code = request.form['join_code']
            else:
                config.join_code = None
        else:
            config.join_code = None
        config.allow_signup = 'allow_signup' in request.form
        config.approve_posts = 'approve_posts' in request.form
        return redirect(routes["admin_dashboard"])

# a table of all registered users on the site
@admin.route(routes["users"])
def user_list():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    users, is_last_page = paged_users(page, search_type=SearchType.ALL)
    return render_template('admin/users/users.html', routes=routes, user=local_user, users=users,
                           is_last_page=is_last_page, page=page, is_admin_view=False)

# an admin-facing list of all users on the site, including additional options
@admin.route(routes["admin_users"])
def admin_user_list():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    users, is_last_page = paged_users(page, search_type=SearchType.ALL)
    return render_template('admin/users/users.html', routes=routes, user=local_user, users=users,
                           is_last_page=is_last_page, page=page, is_admin_view=True)

# a form to select punishments (ban, mute, permaban) with an expiration and reason to be displayed to the user
# you can also use it to lift punishments by selecting 'none'
@admin.route(routes["admin_user_punish"].format("<username>"), methods=['GET', 'POST'])
def user_punishment(username):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)

    search_user = User.read(connection, username)
    if request.method == "GET":
        return render_template("admin/users/punish.html", user=local_user, routes=routes, search_user=search_user,
                               PunishmentType=PunishmentType)
    else:
        # set user punishment
        try:
            search_user.punishment_status = PunishmentType(request.form.get('punishment'))
        except ValueError:
            return render_template("admin/users/punish.html", user=local_user, routes=routes, search_user=search_user,
                                   PunishmentType=PunishmentType)

        search_user.punishment_reason = request.form.get('reason')
        if  search_user.punishment_status == PunishmentType.PERMABAN:
            search_user.clear_data()
        elif 'expiration' in request.form:
            search_user.punishment_expiration = datetime.datetime.strptime(request.form.get('expiration'), "%Y-%m-%dT%H:%M")

        return redirect(search_user.url)

# a menu to change user permissions level (member, moderator, or admin)
@admin.route(routes["admin_user_change_role"].format("<username>"), methods=['GET', 'POST'])
def user_change_role(username):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user, True)

    search_user = User.read(connection, username)
    if request.method == "GET":
        return render_template("admin/users/role.html", user=local_user, routes=routes, search_user=search_user,
                               Role=Role)
    else:
        # set user punishment
        try:
            search_user.role = Role(request.form.get('role'))
        except ValueError:
            return render_template("admin/users/role.html", user=local_user, routes=routes, search_user=search_user,
                                   Role=Role)

        return redirect(search_user.url)

# an admin menu to confirm censoring an inappropriate user bio
@admin.route(routes["admin_user_censor_bio"].format("<username>"), methods=['GET', 'POST'])
def user_censor_bio(username):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)

    search_user = User.read(connection, username)
    if request.method == "GET":
        return render_template("admin/users/censor_bio.html", user=local_user, routes=routes, search_user=search_user)
    else:
        search_user.bio = "[CENSORED BY ADMIN]"
        return redirect(search_user.url)

# an admin menu to confirm deleting a post
@admin.route(routes["admin_post_delete"].format("<int:post_id>"), methods=['GET', 'POST'])
def post_delete(post_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)

    post = Post.read(connection, post_id)
    if request.method == "GET":
        return render_template("admin/posts/delete.html", user=local_user, routes=routes, post=post)
    else:
        post.delete()
        return redirect(routes["admin_dashboard"])

# an admin menu to confirm deleting a comment
@admin.route(routes["admin_comment_delete"].format("<int:comment_id>"), methods=['GET', 'POST'])
def comment_delete(comment_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)

    comment = Comment.read(connection, comment_id)
    if request.method == "GET":
        return render_template("admin/comments/delete.html", user=local_user, routes=routes, comment=comment)
    else:
        post = Post.read(connection, comment.comment_page)
        comment.delete()
        return redirect(post.url)

# an admin view that lists the previously connected IP's in a table
@admin.route(routes["admin_client_list"])
def client_list():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    clients, is_last_page = paged_clients(page, search_type=SearchType.ALL)
    return render_template('admin/clients/clients.html', routes=routes, user=local_user, clients=clients, is_last_page=is_last_page, page=page)

# a form to select IP punishments (ban, mute) with an expiration and reason to be displayed to the user
# you can also use it to lift punishments by selecting 'none'
@admin.route(routes["admin_client_punish"].format("<ip>"), methods=['GET', 'POST'])
def client_punishment(ip):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)

    client = Client(connection, ip)
    if request.method == "GET":
        return render_template("admin/clients/punish.html", user=local_user, routes=routes, client=client, PunishmentType=PunishmentType)
    else:
        # set user punishment
        try:
            client.punishment_status = PunishmentType(request.form.get('punishment'))
        except ValueError:
            return render_template("admin/clients/punish.html", user=local_user, routes=routes, client=client,
                                   PunishmentType=PunishmentType)

        client.punishment_reason = request.form.get('reason')
        if client.punishment_status == PunishmentType.PERMABAN: # you can't permaban a client.....
            return render_template("admin/clients/punish.html", user=local_user, routes=routes, client=client,
                                   PunishmentType=PunishmentType)
        elif 'expiration' in request.form:
            client.punishment_expiration = datetime.datetime.strptime(request.form.get('expiration'), "%Y-%m-%dT%H:%M")

        return redirect(routes["admin_dashboard"])

# a table that displays relevant info and currently online clients connecting to the server from a specific IP
@admin.route(routes["admin_client_sessions"].format("<ip>"))
def client_sessions(ip):
    # get db, user, client
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    client = Client(connection, ip)

    # pagination of client-sessions
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    sessions, is_last_page = paged_sessions(page, search_client=client)
    return render_template('admin/clients/sessions.html', routes=routes, user=local_user,
                           sessions=sessions, is_last_page=is_last_page, page=page, client=client, user_view=False)

# a table that displays relevant info and currently online clients connecting to the server from a specific user
@admin.route(routes["admin_user_sessions"].format("<username>"))
def user_sessions(username):
    # get db, user, search user
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    search_user = User.read(connection, username)

    # pagination of client-sessions
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    sessions, is_last_page = paged_sessions(page, search_user=search_user)
    return render_template('admin/users/sessions.html', routes=routes, user=local_user,
                           sessions=sessions, is_last_page=is_last_page, page=page, search_user=search_user, user_view=False)

# menu to delete an auth token, logging out a user
@admin.route(routes["admin_session_delete"].format("<token_id>"), methods=["GET", "POST"])
def session_delete(token_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    token = Token.read(connection, token_id)
    if request.method == "GET":
        return render_template("admin/sessions/delete.html", user=local_user, routes=routes, token=token)
    else:
        search_user = token.user
        token.delete()
        return redirect(search_user.url)