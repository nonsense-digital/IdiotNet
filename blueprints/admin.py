from flask import Blueprint, render_template, abort, request, redirect, make_response
from helpers.auth import *
from helpers.db import *
from helpers.listings import paged_posts, SearchType, search_posts
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

@admin.route(routes["admin-dashboard"])
def dashboard():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)
    return render_template("admin/index.html", user=local_user, routes=routes)

@admin.route(routes["admin-user-ban"].format("<username>"), methods=['GET', 'POST'])
def ban_user(username):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)

    search_user = User.read(connection, username)
    if request.method == "GET":
        punishment_name = search_user.punishment_status.value.capitalize()
        punishment_suffix = "ing" if (search_user.punishment_status == PunishmentType.MUTE) else "nning"
        punishment_title = f'Confirm {punishment_name}{punishment_suffix} {search_user.username}'
        return render_template("admin/users/ban.html", user=local_user, routes=routes, search_user=search_user, punishment_name=punishment_name, punishment_title=punishment_title)
    else:
        # get punishment parameters
        valid_until = datetime.datetime.strptime(request.form.get('valid_until'), "%Y-%m-%dT%H:%M")
        print(valid_until)
        reason = request.form.get('reason')

        # set user punishment
        search_user.punishment_status = PunishmentType.BAN
        search_user.punishment_expiration = valid_until
        search_user.punishment_reason = reason
        return redirect(routes["admin-dashboard"])

