import os
import psycopg2
from flask import g, current_app

from models.config import Config

DB_VERSION = "1.0"

# check database version to make sure it is up to date
def check_db_version():
    global DB_VERSION
    connection = get_db_connection()

    try:
        config = Config.get(connection)
        connection.close()
        if config.version != DB_VERSION:
            current_app.logger.fatal(f"Expected database version {DB_VERSION}, got {config.version} instead.")
            raise RuntimeError(f"Expected database version {DB_VERSION}, got {config.version} instead.")
    except Exception as error:
        current_app.logger.error(f"Invalid database schema. {error}")
        raise RuntimeError(f"Invalid database schema. {error}")

# get connection and/or local user
# do use_g=False if you aren't in a request context
def get_db_connection(use_g:bool=True):
    if not use_g or (('db' not in g) and use_g): # only require that db isn't in g if use_g is true
        try:
            # connect to db and return connection
            connection = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host= os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                sslmode=os.getenv("DB_SSL_MODE")
            )

            if use_g:
                g.db = connection
            return connection
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