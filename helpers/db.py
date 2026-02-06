import os
import psycopg2
from flask import g, current_app

DB_VERSION = "1.0"

# check database version to make sure it is up to date
def check_db_version():
    global DB_VERSION
    connection = get_db_connection()

    cursor = connection.cursor()
    try:
        cursor.execute("SELECT value FROM config WHERE key = 'version'")
        database_version = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        if database_version != DB_VERSION:
            current_app.logger.fatal(f"Expected database version {DB_VERSION}, got {database_version} instead.")
            raise RuntimeError(f"Expected database version {DB_VERSION}, got {database_version} instead.")
    except Exception as error:
        cursor.close()
        connection.close()
        current_app.logger.error(f"Invalid database schema. {error}")
        raise RuntimeError(f"Invalid database schema. {error}")


# get connection and/or local user
def get_db_connection():
    if 'db' not in g:
        try:
            # connect to db and return connection
            connection = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host= os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )

            g.db = connection
            return g.db
        except (Exception, psycopg2.Error) as error:
            current_app.logger.error(f"An error occurred while connecting to the database: {error}")
    else:
        # return the pre-existing connection
        return g.db

# closes the database connection
def close_db_connection():
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception as error:
            current_app.logger.error(f"An error occurred while closing the database: {error}")