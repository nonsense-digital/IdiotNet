from flask import Blueprint, render_template, request, redirect
from helpers.auth import *
from helpers.db import *
from models.user import check_password
from routes import routes

settings = Blueprint('settings', __name__, template_folder='../templates')

@settings.route(routes["change_password"], methods=['GET', 'POST'])
def change_password():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)


    if not local_user:
        return redirect(routes["home"])
    else:
        if request.method == 'GET':
            return render_template("settings/password.html", routes=routes, user=local_user, error_message=None)
        else:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            verify_new_password = request.form.get('verify_new_password')

            password_error = check_password(new_password, verify_new_password, old_password)
            if password_error is not None:
                current_app.logger.warning(f"[IP {request.remote_addr}] {local_user.username} failed to change password: {password_error}")
                return render_template("settings/password.html", routes=routes, user=local_user,
                                       error_message=password_error)

            if old_password == local_user.password_hash:
                local_user.password_hash = new_password
                current_app.logger.info(
                    f"[IP {request.remote_addr}] {local_user.username} changed their password successfully")
                return redirect(routes["user"].format(local_user.username))
            else:
                current_app.logger.warning(
                    f"[IP {request.remote_addr}] {local_user.username} failed to change password: Incorrect old password")
                return render_template("settings/password.html", routes=routes, user=local_user,
                                       error_message=f'Incorrect old password')