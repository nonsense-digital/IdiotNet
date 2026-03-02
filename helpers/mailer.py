import os
from enum import Enum
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from flask import current_app
from jinja2 import Environment, FileSystemLoader

from helpers.auth import hash_password
from models.user import User
from models.verify import Verify
from routes import routes
import sys
from smtplib import SMTP_SSL as SMTP, SMTPDataError
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# get config constants
SERVER_ADDR = os.getenv('SERVER_ADDR')

# types of transactional emails that can be used
class EmailType(Enum):
    VERIFY_EMAIL = "verify_email" # first-time email verification on account creation
    VERIFY_CHANGE_EMAIL = "verify_change_email" # email verification when user wants to change emails
    PUNISHMENT = "punishment" # notification of ban/mute/permaban punishments or a pardon
    PASSWORD_RESET = "password_reset" # used when user selects "forgot password" in login menu

# sends an email to the address on a specific user
def send_user_email(recipient:User, email_type:EmailType, verify=None):
    # format the email template with user/email information
    content = get_template(email_type, verify=verify, user=recipient)

    # determine destination
    # for email verifications, the new email hasn't been added to the user yet, so it is stored in the verify object
    # otherwise, the destination email should be stored in the actual user object
    destination = verify.email if verify else recipient.email

    # send the email!
    send_email(destination, content)

# Source - https://stackoverflow.com/a/64890
# Posted by Vincent Marchetti, modified by community. See post 'Timeline' for change history
# Retrieved 2026-02-13, License - CC BY-SA 4.0
# also thanks to https://documentation.mailgun.com/docs/mailgun/user-manual/sending-messages/send-smtp
def send_email(destination:str, content:str):
    # format HTML and extract the email subject from the HTML
    soup = BeautifulSoup(content, 'html.parser')
    subject = soup.title.string

    # get email parameters
    email_server = os.getenv('EMAIL_SERVER')
    username = os.getenv('EMAIL_ADDR')
    password = os.getenv('EMAIL_PASSWORD')
    msg = MIMEText(content, 'html')
    msg['Subject'] = subject
    msg['From'] = username

    # attempt to send the email
    conn = SMTP(email_server)
    conn.set_debuglevel(False)
    conn.login(username, password)
    try:
        conn.sendmail(username, destination, msg.as_string())
    except SMTPDataError as e:
        raise RuntimeError(f"Could not send email to {destination}: {e}")
    finally:
        conn.quit()

# for the verification email on account creation
# this is necessary because if we created an account but the email didn't go through, the email would be useless
# so this function will create a verification token and attempt to send the email
# if the email doesn't go through, delete the token and don't create a user
def send_new_account_email(connection, username:str, password_hash:bytes, email:str):
    verify = Verify.create(connection, -1, email) # temporarily set to -1 since we haven't created the user
    content = get_template(EmailType.VERIFY_EMAIL, verify=verify, username=username) # get email template

    # attempt to send the email
    try:
        send_email(email, content) # if this works, then keep going
        user = User.create(connection, username, password_hash, email=email) # we are OK to create the account
        return verify
    except RuntimeError as e:
        verify.delete() # cleanup: delete the verification token because it's not linked yet
        raise RuntimeError(e)


# thanks for the help from https://realpython.com/primer-on-jinja-templating/#use-an-external-file-as-a-template
# gets a formatted HTML template for emailing
def get_template(email_type:EmailType, **kwargs):
    global SERVER_ADDR

    if email_type == EmailType.PASSWORD_RESET:
        raise NotImplementedError("Password reset functionality has not been implemented")

    # read email template file for templating
    current_file = Path(__file__).resolve() # get current file
    template_dir = current_file.parent.parent / "templates" / "email" # get template directory
    env = Environment(loader=FileSystemLoader(str(template_dir))) # get jinja env
    template = env.get_template(f'{email_type.value}.html')

    # format with inputs and return
    content = template.render(email_type=email_type, routes=routes,
                              server_addr=SERVER_ADDR, **kwargs)
    return content