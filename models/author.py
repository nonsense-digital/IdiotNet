from routes import routes

# intermediary module for a simple reference to a user without excessive db queries or circular imports
class Author:
    def __init__(self, connection, user_id:int):
        self.user_id = user_id
        cursor = connection.cursor()
        cursor.execute('select username from users where id = %s', (self.user_id,))
        self.username = cursor.fetchone()[0]
        self.url = routes['user'].format(self.username)
        cursor.close()