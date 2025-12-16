import datetime

from routes import routes
from models.comment import Comment
from enum import Enum
from models.author import Author

class SortMethod(Enum):
    LATEST = 0
    OLDEST = 1
    POPULAR = 2
    RELEVANT = 3
    LIKED = 4

# make sure a post title is not empty (excluding spaces)
def check_empty(text:str):
    withoutSpaces = ""
    for char in text:
        if char != " ":
            withoutSpaces += char
    return withoutSpaces == ""

class Post:
    # --- CONSTRUCTORS ---
    # These are different ways that a Post object can be created.

    # Creates an empty post object.
    # If you are trying to create a new post in the database, use publish() instead.
    # If you are trying to read a pre-existing post from the database, use read() instead
    # If you want a list of the latest posts, use latest()
    def __init__(self, post_id:int):
        self.post_id = post_id
        self.connection = None
        self.__title__ = None
        self.__content__ = None
        self.__author__ = None
        self.__date_posted__ = None
        self.__date_modified__ = None

    # Creates a new post, adds it to the database, and returns the resulting post object
    @staticmethod
    def publish(connection, title:str, content:str, author:int):
        # insert a new post into the database
        date_posted = datetime.datetime.now()
        cursor = connection.cursor()
        query = "INSERT INTO posts (title, content, author, date_posted) VALUES (%s, %s, %s, %s) RETURNING id"
        data = (title, content, author, date_posted)
        cursor.execute(query, data)
        connection.commit()


        # create the new post object
        p = Post(cursor.fetchone()[0])
        p.connection = connection
        p.__title__ = title
        p.__content__ = content
        p.__author__ = Author(connection, author)
        p.__date_posted__ = date_posted
        cursor.close()
        return p

    # Reads a post from the database and returns it as a post object
    @staticmethod
    def read(connection, post_id:int):
        try:
            p = Post(post_id)
            p.connection = connection
            p.update_values()
            return p
        except NameError:
            raise NameError("Post not found")
        except TypeError:
            raise NameError("Post not found")

    # Gets a list of posts, sorted by age or by popularity
    @staticmethod
    def latest(connection, count:int, offset:int=0, sort_by:SortMethod=SortMethod.LATEST):
        cursor = connection.cursor()
        if sort_by == SortMethod.LATEST:
            query = "SELECT id FROM posts ORDER BY date_posted DESC OFFSET %s LIMIT %s"
        elif sort_by == SortMethod.OLDEST:
            query = "SELECT id FROM posts ORDER BY date_posted OFFSET %s LIMIT %s"
        elif sort_by == SortMethod.POPULAR:
            raise NotImplementedError("Sort by popularity not implemented.")
        else:
            raise ValueError("Sorting method not specified.")
        cursor.execute(query, (offset, count))
        data = cursor.fetchall()
        posts = []
        for record in data:
            p = Post.read(connection, record[0])
            posts.append(p)
        return posts

    @staticmethod
    def search(connection, term:str, count:int, offset:int=0):
        print(f"Query: {term}, Count: {count}, Offset: {offset}")
        # query database for relevant posts
        cursor = connection.cursor()
        query = 'SELECT id, title FROM posts WHERE ts_nostop @@ phraseto_tsquery(\'public.english_nostop\', %s) ORDER BY ts_rank(ts_nostop, websearch_to_tsquery(\'public.english_nostop\', %s)) DESC OFFSET %s LIMIT %s;'
        cursor.execute(query, (term, term, offset, count))
        results = cursor.fetchall()
        cursor.close()
        #print(f"Term: {term} count: {count} offset: {offset} reuslts: {results}")
        # convert to post objects
        posts = []
        for result in results:
            p = Post.read(connection, result[0])
            posts.append(p)
        return posts






    # --- GETTERS AND SETTERS ----
    # When a Post object's atomic properties (title, content, date posted, etc.) are called, a getter function retrieves them from its private field.
    # When an atomic value is modified, the change is sent to the database with a setter function.
    # There are also getters that query the database for list objects (comments and attachments) but no setters, as these are read-only.

    @property
    def title(self):
        return self.__title__

    @title.setter
    def title(self, title):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE posts set title = %s where id = %s", (title, self.post_id))
        self.__title__ = title
        cursor.close()

    @property
    def content(self):
        return self.__content__

    @content.setter
    def content(self, content):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE posts set content = %s where id = %s", (content, self.post_id))
        self.__content__ = content
        cursor.close()

    @property
    def author(self):
        return self.__author__

    @author.setter
    def author(self, author):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE posts set author = %s where id = %s", (author, self.post_id))
        self.__author__ = Author(self.connection, author)
        cursor.close()

    @property
    def date_posted(self):
        return self.__date_posted__

    @date_posted.setter
    def date_posted(self, date_posted):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE posts set date_posted = %s where id = %s", (date_posted, self.post_id))
        self.__date_posted__ = date_posted
        cursor.close()

    @property
    def date_modified(self):
        return self.__date_modified__

    @date_modified.setter
    def date_modified(self, date_modified):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE posts set date_modified = %s where id = %s", (date_modified, self.post_id))
        self.__date_modified__ = date_modified
        cursor.close()

    @property
    def url(self):
        return routes["post"].format(self.post_id)

    # updates all atomic values
    def update_values(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = %s", (self.post_id,))
        try:
            result = cursor.fetchall()[0]
            self.__title__ = result[1]
            self.__content__ = result[2]
            self.__author__ = Author(self.connection, result[3])
            self.__date_posted__ = result[4]
            self.__date_modified__ = result[5]
        except IndexError:
            raise NameError("Post not found")

    # Gets the post's comments from the database
    @property
    def comments(self):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT id FROM comments WHERE comment_page = %s AND comment_type = 0 AND root_comment = -1 ORDER BY date_posted",
            (self.post_id,))
        comments = []
        result = cursor.fetchall()
        for comment_id in result:
            try:
                comments.append(Comment.read(self.connection, comment_id[0]))
            except NameError:
                pass
        cursor.close()
        return comments

    # Gets all post's comments, including replies
    @property
    def all_comments(self):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT id FROM comments WHERE comment_page = %s AND comment_type = 0 ORDER BY date_posted",
            (self.post_id,))
        comments = []
        result = cursor.fetchall()
        for comment_id in result:
            try:
                comments.append(Comment.read(self.connection, comment_id[0]))
            except NameError:
                pass
        cursor.close()
        return comments

    # gets the likes of the post
    @property
    def likes(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id from likes WHERE liked = %s", (self.post_id,))
        results = cursor.fetchall()
        cursor.close()
        return len(results)