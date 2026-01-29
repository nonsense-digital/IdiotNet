from flask import Blueprint, render_template, abort, request, redirect, make_response
from helpers.auth import *
from helpers.db import *
from helpers.listings import paged_posts, SearchType, search_posts, paged_clients
from models.client import Client
from models.post import Post
from models.user import User, check_username, check_password
from models.permissions import Role, PunishmentType
from routes import routes

admin = Blueprint('admin', __name__, template_folder='../templates')

def check_admin(local_user:User):
    if local_user is None:
        abort(403)
    elif local_user.role == Role.MEMBER:
        abort(403)

@admin.route(routes["admin_dashboard"])
def dashboard():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    return render_template("admin/index.html", user=local_user, routes=routes)

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

        return redirect(routes["admin_dashboard"])

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