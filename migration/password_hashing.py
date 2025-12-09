import os
import psycopg2
from models.user import User
from helpers.auth import hash_password
from dotenv import load_dotenv

# RUN THIS FILE IF YOUR PASSWORDS ARE STILL IN PLAINTEXT!
# If your passwords are already hashed, then this will break all the accounts

# also run this: alter table users alter column password_hash type bytea using password_hash::bytea;

def main():
    load_dotenv()

    # get a database connection from environment variables
    connection = psycopg2.connect(
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host= os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT")
                )

    # get a list of all users
    cursor = connection.cursor()
    cursor.execute("SELECT id from users")
    data = cursor.fetchall()
    cursor.close()

    # hash password for each user
    for x in data:
        user_id = x[0]
        user = User.read(connection, user_id)
        password = user.password_hash
        password_hash = hash_password(password)
        user.password_hash = password_hash
        print(f"Changed password from plaintext {password} to hash/salt {password_hash}")

if __name__ == '__main__':
    main()