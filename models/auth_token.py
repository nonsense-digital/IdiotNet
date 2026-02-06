from datetime import datetime, timedelta
import uuid
from models.user import User


class Token:
    # --- CONSTRUCTORS ---
    # These are different ways that an Auth Token object can be created.

    # Creates an empty token object.
    # If you are trying to create a new token in the database, use create() instead.
    # If you are trying to read a pre-existing token from the database, use read() instead
    def __init__(self, user_id):
        self.token_id = None
        self.connection = None
        self.__user_id__ = user_id
        self.__valid_until__ = None
        self.__is_deleted__ = False
        self.__client_ip__ = None


    # creates a new token and adds it to the database
    @staticmethod
    def create(connection, user_id:int, client_ip:str):
        try:
            user = User.read(connection, user_id)
        except Exception as e:
            raise NameError("User not found")
        t = Token(user_id)
        t.connection = connection
        t.token_id = str(uuid.uuid4())
        t.__client_ip__ = client_ip
        t.__valid_until__ = datetime.now() + timedelta(days=7)
        cursor = connection.cursor()
        query = "INSERT INTO tokens (id, user_id, valid_until, client) VALUES (%s, %s, %s, %s)"
        data = (t.token_id, t.__user_id__, t.__valid_until__, t.__client_ip__)
        cursor.execute(query, data)
        connection.commit()
        cursor.close()
        return t

    # reads a token from the database
    @staticmethod
    def read(connection, token_id:str):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tokens WHERE id = %s", (token_id,))
        data = cursor.fetchone()
        if data is None:
            raise NameError("Token not found")
        else:
            t = Token(data[1])
            t.connection = connection
            t.token_id = token_id
            t.__valid_until__ = data[2]
            t.__client_ip__ = data[3]
            return t

    # --- GETTERS AND SETTERS ----
    # All token values, except for expiration date, are read-only, and so they have no setters
    @property
    def user_id(self):
        if self.__is_deleted__:
            raise NameError(f"Token {self.token_id} has already been deleted.")
        return self.__user_id__

    @property
    def user(self):
        return User.read(self.connection, self.user_id)

    @property
    def valid_until(self):
        if self.__is_deleted__:
            raise NameError(f"Token {self.token_id} has already been deleted.")
        return self.__valid_until__

    @property
    def client_ip(self):
        return self.__client_ip__

    # Every time a user views a page on IdiotNet, extend their login time for 7 more days
    def extend_lifetime(self, connection):
        if self.__is_deleted__:
            raise NameError(f"Token {self.token_id} has already been deleted.")

        cursor = connection.cursor()
        valid_until = datetime.now() + timedelta(days=7)
        cursor.execute("UPDATE tokens SET valid_until = %s WHERE id = %s", (valid_until, self.token_id))
        connection.commit()
        cursor.close()
        self.__valid_until__ = valid_until

    # --- TOKEN-SPECIFIC METHODS ---
    # These are various token-specific actions one can perform

    # delete the token (effectively logging the user out)
    def delete(self):
        if self.__is_deleted__:
            raise NameError(f"Token {self.token_id} has already been deleted.")
        # Delete the token from the database
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM tokens WHERE id = %s", (self.token_id,))
        self.connection.commit()
        self.__is_deleted__ = True