import datetime
from models.author import Author

class Comment:
    # --- CONSTRUCTORS ---
    # These are different ways that a Comment object can be created.

    # Creates an empty comment object.
    # If you are trying to create a new comment in the database, use publish() instead.
    # If you are trying to read a pre-existing comment from the database, use read() instead
    def __init__(self, comment_id:int):
        self.comment_id = comment_id
        self.connection = None
        self.__content__ = None
        self.__author__ = None
        self.__root_comment__ = None
        self.__comment_type__ = None
        self.__date_posted__ = None
        self.__comment_page__ = None

    # creates a new comment object, adds it to the database, and returns the resulting comment object
    @staticmethod
    def publish(connection, content:str, author:int, comment_page:int, comment_type:int=0, root_comment:int=-1):
        # insert a new post into the database
        date_posted = datetime.datetime.now()
        cursor = connection.cursor()
        query = "INSERT INTO comments (content, author, root_comment, date_posted, comment_type, comment_page) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
        data = (content, author, root_comment, date_posted, comment_type, comment_page)
        cursor.execute(query, data)
        connection.commit()

        # create the new post object
        c = Comment(cursor.fetchone()[0])
        c.__content__ = content
        c.__author__ = Author(connection, author)
        c.__root_comment__ = None
        c.__comment_type__ = None
        c.__date_posted__ = None
        c.__comment_page__ = None
        cursor.close()
        return c

    # read a comment from the database and create an object from it
    @staticmethod
    def read(connection, post_id:int):
        try:
            c = Comment(post_id)
            c.connection = connection
            c.update_values()
            return c
        except NameError:
            raise NameError("Comment not found")
        except TypeError:
            raise NameError("Comment not found")

    # --- GETTERS AND SETTERS ----
    # When a Comment object's atomic properties (content, author, page id, etc.) are called, a getter function retrieves them from its private field.
    # When an atomic value is modified, the change is sent to the database with a setter function.
    # There are also getters that query the database for list objects (replies) but no setters, as these are read-only.

    @property
    def content(self):
        return self.__content__
    @content.setter
    def content(self, content:str):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE comments set content = %s where id = %s", (content, self.comment_id))
        self.__content__ = content
        cursor.close()

    @property
    def author(self):
        return self.__author__
    @author.setter
    def author(self, author:int):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE comments set author = %s where id = %s", (author, self.comment_id))
        self.__content__ = Author(self.connection, author)
        cursor.close()

    @property
    def root_comment(self):
        return self.__root_comment__
    @root_comment.setter
    def root_comment(self, root_comment:int):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE comments set root_comment = %s where id = %s", (root_comment, self.comment_id))
        self.__root_comment__ = root_comment
        cursor.close()

    @property
    def date_posted(self):
        return self.__date_posted__
    @date_posted.setter
    def date_posted(self, date_posted:datetime.datetime):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE comments set date_posted = %s where id = %s", (date_posted, self.comment_id))
        self.__date_posted__ = date_posted
        cursor.close()

    @property
    def comment_type(self):
        return self.__comment_type__
    @comment_type.setter
    def comment_type(self, comment_type:int):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE comments set comment_type = %s where id = %s", (comment_type, self.comment_id))
        self.__comment_type__ = comment_type
        cursor.close()

    @property
    def comment_page(self):
        return self.__comment_page__
    @comment_page.setter
    def comment_page(self, comment_page:int):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE comments set comment_page = %s where id = %s", (comment_page, self.comment_id))
        self.__comment_page__ = comment_page
        cursor.close()

    # update all atomic values
    def update_values(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * from comments WHERE id = %s", (self.comment_id,))
        try:
            result = cursor.fetchone()
            self.__content__ = result[1]
            self.__author__ = Author(self.connection, result[2])
            self.__root_comment__ = result[3]
            self.__date_posted__ = result[4]
            self.__comment_type__ = result[5]
            self.__comment_page__ = result[6]
        except IndexError:
            raise NameError("Comment not found")

    # Get all the replies to the comment
    @property
    def replies(self):
        if self.__root_comment__ == -1:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id FROM comments WHERE root_comment = %s ORDER BY date_posted",
                (self.comment_id,))
            replies = []
            for comment_id in cursor.fetchall():
                try:
                    replies.append(Comment.read(self.connection, comment_id[0]))
                except NameError:
                    pass
            cursor.close()
            return replies
        else:
            raise ValueError("Cannot get replies from non-root comment")









