import datetime

from user import User

class Comment:
    def __init__(self, content, author:int, comment_page, comment_type=0, root_comment=-1):
        self.comment_id = 0
        self.content = content
        self.author = author
        self.author_name = None
        self.root_comment = root_comment
        self.comment_type = comment_type
        self.date_posted = None
        self.comment_page = comment_page
        self.is_published = False
        self.is_root = root_comment == -1
        self.replies = []

    def publish(self, connection, user):
        if not self.is_published:
            self.date_posted = datetime.datetime.now()
            self.is_published = True
            self.author_name = user.username
            cursor = connection.cursor()
            query = "INSERT INTO comments (content, author, root_comment, date_posted, comment_type, comment_page) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
            data = (self.content, self.author, self.root_comment, self.date_posted, self.comment_type, self.comment_page)
            cursor.execute(query, data)
            connection.commit()
            self.comment_id = cursor.fetchone()[0]
            cursor.close()

        else:
            raise Exception("Post is already published")

    @staticmethod
    def read(connection, comment_id):
        cursor = connection.cursor()
        query = "SELECT * FROM comments WHERE id=%s"
        cursor.execute(query, (comment_id,))
        data = cursor.fetchone()
        if data is None:
            raise NameError("Comment not found")
        else:
            c = Comment(data[1], data[2], data[6], data[5], data[3])
            c.comment_id = data[0]
            c.author_name = User.read(connection, data[2]).username
            c.date_posted = data[4]
            cursor.execute("SELECT id FROM comments WHERE root_comment = %s ORDER BY date_posted",
                           (c.comment_id,))
            c.replies = []
            for comment_id in cursor.fetchall():
                try:
                    c.replies.append(Comment.read(connection, comment_id[0]))
                except NameError:
                    pass
            return c

