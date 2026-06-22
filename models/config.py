import datetime
from flask import g

from helpers.misc import null_pack
from routes import routes
from models.permissions import Role, PunishmentType

class Config:
    # --- CONSTRUCTORS ---
    # Gets a reference to the server's configuration
    # or use the appcontext for efficiency
    def __init__(self, connection):
        # define fields
        self.connection = connection
        self.__config__ = {}
        try:
            self.update_values()
            g.config = self
        except ValueError:
            raise ValueError("Invalid server configuration")

    # we only need one instance of this model because there is only one configuration
    # so we can store it in the appcontext
    @staticmethod
    def get(connection):
        if 'config' in g:
            return g.get('config')
        else:
            return Config(connection)

    # --- GETTERS AND SETTERS ----
    # Simple key-value getters and setters for the database

    # string representation of the config, useful for logging
    def __str__(self):
        return f'placeholder'

    def update_values(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT key, value FROM config')
        for key, value in cursor.fetchall():
            self.__config__[key] = value
        cursor.close()

    @property
    def version(self):
        return self.__version__

    @property
    def join_code_required(self):
        return self.__config__['join_code'] is not None

    @property
    def has_support_email(self):
        return self.__config__['support_email'] is not None

    @property
    def has_announcement_banner(self):
        return self.__config__['announcement_banner'] is not None

    # get any config value
    def __getattr__(self, key):
        if key == 'connection' or key == '__config__': # getattr doesn't apply to connection and config
            return super().__getattribute__(key)

        if key != 'connection' and key != '__config__' and key in self.__config__.keys():
            data = self.__config__[key]
            if data not in ('true', 'false'):
                return data
            else:
                return data == 'true'
        else:
            return super().__getattribute__(key)

    # set any config value
    def __setattr__(self, key, value):
        if key == 'connection' or key == '__config__': # setattr doesn't apply to connection and config
            super().__setattr__(key, value)
            return

        if key in self.__config__.keys():
            cursor = self.connection.cursor()
            cursor.execute("UPDATE config SET value = %s WHERE key = %s", (value, key))
            self.connection.commit()
            cursor.close()
            self.__config__[key] = value

        else:
            super().__setattr__(key, value)