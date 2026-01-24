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

@admin.route(routes["admin-user-punishment-base"].format("<username>", "<punishment>"), methods=['GET', 'POST'])
def punishment(username, punishment):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    check_admin(local_user)

    punishment = PunishmentType(punishment)
    search_user = User.read(connection, username)
    if request.method == "GET":
        punishment_name = punishment.title
        punishment_title = f'Confirm {punishment_name} for {search_user.username}'
        warning = punishment.warning
        return render_template("admin/users/punish.html", user=local_user, routes=routes, search_user=search_user,
                               punishment_name=punishment_name, punishment_title=punishment_title,
                               warning=warning)
    else:
        # set user punishment
        search_user.punishment_status = punishment
        search_user.punishment_reason = request.form.get('reason')
        if punishment == PunishmentType.PERMABAN:
            search_user.clear_data()
        elif 'valid_until' in request.form:
            search_user.punishment_expiration = datetime.datetime.strptime(request.form.get('valid_until'), "%Y-%m-%dT%H:%M")

        return redirect(routes["admin-dashboard"])