from psycopg2._psycopg import connection

from routes import routes

# simple module for a simple reference to a user without excessive db queries or circular imports
class UserRef:
    def __init__(self, connection, user_id:int):
        self.user_id = user_id
        cursor = connection.cursor()
        cursor.execute('select username from users where id = %s', (self.user_id,))
        try:
            self.username = cursor.fetchone()[0]
            self.url = routes['user'].format(self.username)
        except TypeError:
            self.username = None
            self.url = None
        cursor.close()

    @staticmethod
    def get_id_from_username(self, username:str):
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', username)
        try:
            user_id = int(cursor.fetchone()[0])
            return user_id
        except TypeError:
            raise NameError("User not found")
        except ValueError:
            raise NameError("User not found")