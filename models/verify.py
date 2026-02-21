from datetime import datetime, timedelta
import uuid
from models.user import User

class Verify:
    # --- CONSTRUCTORS ---
    # These are different ways that a verification challenge object can be created.

    # Creates an empty verify object.
    # If you are trying to create a new verify in the database, use create() instead.
    # If you are trying to read a pre-existing verify from the database, use read() instead
    def __init__(self, user_id):
        self.verify_id = None
        self.connection = None
        self.__user_id__ = user_id
        self.__valid_until__ = None
        self.__email__ = None
        self.__is_deleted__ = False

    # creates a new verify and adds it to the database
    @staticmethod
    def create(connection, user_id:int, email:str):
        try:
            user = User.read(connection, user_id)
        except Exception as e:
            raise NameError("User not found")
        v = Verify(user_id)
        v.connection = connection
        v.verify_id = str(uuid.uuid4())
        v.__valid_until__ = datetime.now() + timedelta(days=7) # you get 7 days to verify your email
        v.__email__ = email
        cursor = connection.cursor()
        query = "INSERT INTO verify (id, user_id, valid_until, email) VALUES (%s, %s, %s, %s)"
        data = (v.verify_id, v.__user_id__, v.__valid_until__, v.__email__)
        cursor.execute(query, data)
        connection.commit()
        cursor.close()
        return v

    # reads a verification challenge from the database
    @staticmethod
    def read(connection, verify_id:str):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM verify WHERE id = %s", (verify_id,))
        data = cursor.fetchone()
        if data is None:
            raise NameError("Verification challenge not found")
        else:
            v = Verify(data[1])
            v.connection = connection
            v.verify_id = verify_id
            v.__valid_until__ = data[2]
            v.__email__ = data[3]
            return v

    # used to check if the verification already exists
    @staticmethod
    def check_exists(connection, user_id:int, email:str):
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM verify WHERE user_id = %s AND email = %s", (user_id, email))
        data = cursor.fetchall()
        size = len(data)
        for record in data:
            v = Verify.read(connection, record[0])
            if v.valid_until < datetime.now():
                v.delete()
                size -= 1
        return size != 0

    # --- GETTERS AND SETTERS ----
    # All verify values, except for expiration date, are read-only, and so they have no setters
    @property
    def user_id(self):
        if self.__is_deleted__:
            raise NameError(f"Verification challenge {self.verify_id} has already been deleted.")
        return self.__user_id__

    @property
    def user(self):
        return User.read(self.connection, self.user_id)

    @property
    def valid_until(self):
        if self.__is_deleted__:
            raise NameError(f"Verification challenge {self.verify_id} has already been deleted.")
        return self.__valid_until__

    @property
    def email(self):
        if self.__is_deleted__:
            raise NameError(f"Verification challenge {self.verify_id} has already been deleted.")
        return self.__email__

    # --- VERIFY-SPECIFIC METHODS ---
    # These are various verify-specific actions one can perform

    # delete the verification challenge (effectively logging the user out)
    def delete(self):
        if self.__is_deleted__:
            raise NameError(f"Verification challenge {self.verify_id} has already been deleted.")
        # Delete the verification challenge from the database
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM verify WHERE id = %s", (self.verify_id,))
        self.connection.commit()
        self.__is_deleted__ = True