from datetime import datetime, timedelta
import uuid

from user import User

class Token:
    # --- CONSTRUCTORS ---
    # These are different ways that an Auth Token object can be created.

    # Creates an empty token object.
    # If you are trying to create a new token in the database, use create() instead.
    # If you are trying to read a pre-existing token from the database, use read() instead
    def __init__(self, user_id):
        self.token_id = None
        self.user_id = user_id
        self.valid_until = None

    # creates a new token and adds it to the database
    @staticmethod
    def create(connection, user_id:int):
        try:
            user = User.read(connection, user_id)
        except Exception as e:
            raise Exception("User not found")
        t = Token(user_id)
        t.token_id = str(uuid.uuid4())
        t.valid_until = datetime.now() + timedelta(days=7)
        cursor = connection.cursor()
        query = "INSERT INTO tokens (id, user_id, valid_until) VALUES (%s, %s, %s)"
        data = (t.token_id, t.user_id, t.valid_until)
        cursor.execute(query, data)
        connection.commit()
        cursor.close()
        return t

    @staticmethod
    def read(connection, token_id:str):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tokens WHERE id = %s", (token_id,))
        data = cursor.fetchone()
        if data is None:
            print(f"{token_id} not found")
            raise NameError("Token not found")
        else:
            t = Token(data[1])
            t.token_id = token_id
            t.valid_until = data[2]
            t.is_created = True
            return t
