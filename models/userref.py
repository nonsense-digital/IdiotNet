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