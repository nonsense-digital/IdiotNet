import datetime

from flask import g

from helpers.misc import nullPack
from routes import routes
from models.permissions import Role, PunishmentType

class Config:
    # --- CONSTRUCTORS ---
    # Gets a reference to the server's configuration
    # or use the appcontext for efficiency
    def __init__(self, connection):
        # define fields
        self.connection = connection
        self.__version__ = None
        self.__join_code__ = None
        self.__allow_signup__ = None
        self.__approve_posts__ = None
        self.__support_email__ = None
        self.__announcement_banner__ = None
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
        return (f'(join_code={self.__join_code__}, allow_signup={self.__allow_signup__}, '
                f'approve_posts={self.__approve_posts__}, support_email={self.support_email}, '
                f'announcement_banner={self.announcement_banner})')

    def update_values(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT value FROM config WHERE key = 'version'")
        self.__version__ = nullPack(cursor.fetchone())
        cursor.execute("SELECT value FROM config WHERE key = 'join_code'")
        self.__join_code__ = nullPack(cursor.fetchone())
        cursor.execute("SELECT value FROM config WHERE key = 'allow_signup'")
        self.__allow_signup__ = nullPack(cursor.fetchone())
        cursor.execute("SELECT value FROM config WHERE key = 'approve_posts'")
        self.__approve_posts__ = nullPack(cursor.fetchone())
        cursor.execute("SELECT value FROM config WHERE key = 'support_email'")
        self.__support_email__ = nullPack(cursor.fetchone())
        cursor.execute("SELECT value FROM config WHERE key = 'announcement_banner'")
        self.__announcement_banner__ = nullPack(cursor.fetchone())
        cursor.close()

    @property
    def version(self):
        return self.__version__

    @property
    def join_code_required(self):
        return self.__join_code__ is not None

    @property
    def has_support_email(self):
        return self.__support_email__ is not None

    @property
    def has_announcement_banner(self):
        return self.__announcement_banner__ is not None

    @property
    def join_code(self):
        return self.__join_code__
    @join_code.setter
    def join_code(self, value):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE config SET value = %s WHERE key = 'join_code'", (value,))
        self.connection.commit()
        cursor.close()
        self.__join_code__ = value

    @property
    def allow_signup(self):
        return self.__allow_signup__ == "true"
    @allow_signup.setter
    def allow_signup(self, value):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE config SET value = %s WHERE key = 'allow_signup'", (value,))
        self.connection.commit()
        cursor.close()
        self.__allow_signup__ = value

    @property
    def approve_posts(self):
        return self.__approve_posts__ == "true"
    @approve_posts.setter
    def approve_posts(self, value):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE config SET value = %s WHERE key = 'approve_posts'", (value,))
        self.connection.commit()
        cursor.close()
        self.__approve_posts__ = value

    @property
    def support_email(self):
        return self.__support_email__

    @support_email.setter
    def support_email(self, value):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE config SET value = %s WHERE key = 'support_email'", (value,))
        self.connection.commit()
        cursor.close()
        self.__support_email__ = value

    @property
    def announcement_banner(self):
        return self.__announcement_banner__

    @announcement_banner.setter
    def announcement_banner(self, value):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE config SET value = %s WHERE key = 'announcement_banner'", (value,))
        self.connection.commit()
        cursor.close()
        self.__announcement_banner__ = value