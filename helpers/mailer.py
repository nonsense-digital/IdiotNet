import os
from enum import Enum
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from models.user import User
from models.verify import Verify
from routes import routes
import sys
from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# types of transactional emails that can be used
class EmailType(Enum):
    VERIFY_EMAIL = "verify_email"
    VERIFY_CHANGE_EMAIL = "verify_change_email"
    PUNISHMENT = "punishment"

# sends an email to the address on a specific user
# Source - https://stackoverflow.com/a/64890
# Posted by Vincent Marchetti, modified by community. See post 'Timeline' for change history
# Retrieved 2026-02-13, License - CC BY-SA 4.0
# also thanks to https://documentation.mailgun.com/docs/mailgun/user-manual/sending-messages/send-smtp
def send_email(recipient:User, email_type:EmailType, verify=None):
    # format html and extract the email subject from the html
    server_addr = os.getenv('SERVER_ADDR')
    content = get_template(server_addr, recipient, email_type, verify=verify)
    soup = BeautifulSoup(content, 'html.parser')
    subject = soup.title.string

    # determine destination
    destination = verify.email if verify else recipient.email

    # attempt to send the email
    # for email verifications, the new email hasn't been added to the user yet, so it is stored in the verify object
    # otherwise, the destination email should be stored in the actual user object
    try:
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
        finally:
            conn.quit()

    except Exception as e:
        print(e)
        sys.exit("mail failed; %s" % "CUSTOM_ERROR")  # give an error message

# thanks for the help from https://realpython.com/primer-on-jinja-templating/#use-an-external-file-as-a-template
# gets a formatted HTML template for emailing
def get_template(server_addr:str, recipient:User, email_type:EmailType, verify=None):
    # read email template file for templating
    current_file = Path(__file__).resolve() # get current file
    template_dir = current_file.parent.parent / "templates" / "email" # get template directory
    env = Environment(loader=FileSystemLoader(str(template_dir))) # get jinja env
    template = env.get_template('verify_change_email.html')

    # format with inputs and return
    content = template.render(user=recipient, email_type=email_type, verify=verify, routes=routes,
                              server_addr=server_addr)
    return content