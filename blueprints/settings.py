from flask import Blueprint, render_template, request, redirect, abort

from helpers import mailer
from helpers.auth import *
from helpers.db import *
from helpers.limiter import limiter
from helpers.mailer import EmailType
from models.user import check_password
from models.verify import Verify
from routes import routes

settings = Blueprint('settings', __name__, template_folder='../templates')

# change your password, requiring the old one, the new one, and a confirmation
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

            password_error = check_password(new_password, verify_new_password)
            if password_error is not None:
                current_app.logger.warning(f"[IP {request.remote_addr}] {local_user.username} failed to change password: {password_error}")
                return render_template("settings/password.html", routes=routes, user=local_user,
                                       error_message=password_error)

            if check_password_hash(local_user.password_hash, new_password):
                return render_template("settings/password.html", routes=routes, user=local_user,
                                       error_message="Password is already in use")

            if check_password_hash(local_user.password_hash, old_password):
                local_user.password_hash = hash_password(new_password)
                current_app.logger.info(
                    f"[IP {request.remote_addr}] {local_user.username} changed their password successfully")
                return redirect(routes["user"].format(local_user.username))
            else:
                current_app.logger.warning(
                    f"[IP {request.remote_addr}] {local_user.username} failed to change password: Incorrect old password")
                return render_template("settings/password.html", routes=routes, user=local_user,
                                       error_message=f'Incorrect old password')

# settings menu to change the user's email, requiring email verification
@settings.route(routes["change_email"], methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=["POST"])
def change_email(pre_error=None):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)

    if not local_user:
        return redirect(routes["home"])
    else:
        if request.method == 'GET':
            return render_template("settings/email/index.html", routes=routes, user=local_user, error=pre_error)
        elif request.method == 'POST':
            email = request.form.get('email')
            verify_email = request.form.get('verify_email')

            if email == local_user.email: # display an error, the email is already in use
                return render_template("settings/email/index.html", routes=routes, user=local_user,
                                       error_message='Email already in use')

            # is there already an email sent that hasn't expired yet?
            if Verify.check_exists(connection, local_user.user_id, email):
                return render_template("settings/email/index.html", routes=routes, user=local_user,
                                       error_message='Verification already sent')


            if email == verify_email: # create a verification challenge a notify the user of the email
                # create the verification token and send the email
                verify = Verify.create(connection, local_user.user_id, email)
                server_addr = os.getenv("SERVER_ADDR")
                mailer.send_email(server_addr, local_user, EmailType.VERIFY_CHANGE_EMAIL, verify=verify)
                return render_template("settings/email/await_verify.html", routes=routes,
                                       user=local_user, verify=verify)
            else: # display an error, the emails do not match
                return render_template("settings/email/index.html", routes=routes, user=local_user,
                                       error_message='Emails do not match')

# link that users click on to verify from the email they receive
@settings.route(routes['verify_email'].format("<verify_id>"), methods=['GET'])
def verify_email(verify_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    try:
        verify = Verify.read(connection, verify_id)
        search_user = User.read(connection, verify.user_id)

        # make sure it hasn't expired
        if verify.valid_until < datetime.datetime.now():
            return render_template("settings/email/expired.html", routes=routes,
                                   user=local_user, search_user=search_user, first_time=(search_user.email is None))

        # attempt to set the email and delete the token
        try:
            # set the email and dispose of the verification token
            search_user.email = verify.email
            verify.delete()
            return render_template("settings/email/verify.html", routes=routes, user=local_user, search_user=search_user)
        except NameError:
            abort(404)
    except NameError:
        abort(404)

