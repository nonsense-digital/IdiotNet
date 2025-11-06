import datetime

from routes import routes



class Post:
    def __init__(self, title, content, author:int):
        self.post_id = -1
        self.title = title
        self.content = content
        self.author_id = author
        self.author_name = None
        self.date_posted = None
        self.is_published = False
        self.likes = 0
        self.url = None
        self.comments = []

    def publish(self, connection, user):
        if not self.is_published:
            self.date_posted = datetime.datetime.now()
            self.is_published = True
            self.author_name = user.username
            cursor = connection.cursor()
            query = "INSERT INTO posts (title, content, author, date_posted, likes) VALUES (%s, %s, %s, %s, %s) RETURNING id"
            data = (self.title, self.content, self.author_id, self.date_posted, self.likes,)
            cursor.execute(query, data)
            connection.commit()
            self.post_id = cursor.fetchone()[0]
            user.add_post(connection, self.post_id)
            cursor.close()
            self.url = routes["post"].format(self.post_id)
        else:
            raise Exception("Post is already published")

    def like(self, connection, user, add_like:bool=True):
        user.like_post(connection, self.post_id, add_like)
        cursor = connection.cursor()
        cursor.execute("SELECT likes from posts WHERE id=%s", (self.post_id,))
        self.likes = int(cursor.fetchone()[0])
        self.likes += 1 if add_like else -1
        cursor.execute("UPDATE posts SET likes = %s WHERE id = %s", (self.likes, self.post_id,))
        connection.commit()
        cursor.close()

    def edit_post(self, connection, title, content):
        cursor = connection.cursor()
        cursor.execute("UPDATE posts set (title, content) = (%s, %s) WHERE id=%s", (title, content, (self.post_id,)))
        connection.commit()
        cursor.close()
        self.title = title
        self.content = content


    @staticmethod
    def read(connection, post_id:int):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        data = cursor.fetchone()
        if data is None:
            raise NameError("Post not found")
        else:
            return Post.record_to_object(connection, data)

    @staticmethod
    def record_to_object(connection, record):
        from user import User
        p = Post(title=record[1], content=record[2], author=record[3])
        p.post_id = record[0]
        p.author_name = User.read(connection, record[3]).username
        p.date_posted = record[4]
        p.likes = record[5]
        p.is_published = True
        p.url = routes["post"].format(p.post_id)
        p.comments = []

        # get comments (first comment in 1000 lines of code lol)
        from comment import Comment
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM comments WHERE comment_page = %s AND comment_type = 0 AND root_comment = -1 ORDER BY date_posted",
                       (p.post_id,))
        p.comments = []
        for comment_id in cursor.fetchall():
            try:
                p.comments.append(Comment.read(connection, comment_id[0]))
            except NameError:
                pass
        return p

    @staticmethod
    def latest(connection, count:int, offset:int=0, sort_by:str="latest"):
        cursor = connection.cursor()
        if sort_by == "latest":
            query = "SELECT * FROM posts ORDER BY date_posted DESC OFFSET %s LIMIT %s"
        elif sort_by == "popular":
            query = "SELECT * FROM posts ORDER BY likes DESC OFFSET %s LIMIT %s"
        else:
            query = "SELECT * FROM posts ORDER BY date_posted DESC OFFSET %s LIMIT %s"
        cursor.execute(query, (offset, count))
        data = cursor.fetchall()
        posts = []
        for record in data:
            p = Post.record_to_object(connection, record)
            posts.append(p)
        return posts
