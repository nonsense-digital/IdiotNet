import datetime

from post import Post
from routes import routes

# Characters allowed in Usernames
ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz1234567890_"


def check_username(username: str):
    # Checks a username to make sure it has the correct format
    global ALLOWED_CHARS
    if username == "":
        return "Username is required"
    elif len(username) > 15:
        return "Username limit is 15 characters"
    else:
        for char in username:
            if char.lower() not in ALLOWED_CHARS:
                return 'Only alphanumeric characters and underscores are allowed in usernames'
    return None


def check_password(password: str, verify_password: str, previous_password: str = None):
    # Checks a password to make sure it has the correct format, matches the verify password, and is not the same as the previous_password (if specified)
    if password == "":
        return "Password is required"
    elif len(password) > 100:
        return "Passwords limit is 100 characters"
    elif verify_password != password:
        return "Passwords do not match"
    elif password == previous_password and previous_password is not None:
        return "Password is already in use"
    else:
        return None

class User:
    # --- CONSTRUCTORS ---
    # These are different ways that a User object can be created.

    # Creates an empty user object.
    # If you are trying to create a new user in the database, use create() instead.
    # If you are trying to read a pre-existing user from the database, use read() instead
    def __init__(self, user_id:int):
        self.user_id = user_id
        self.connection = None
        self.__username__ = None
        self.__email__ = None
        self.__date_created__ = None
        self.__password_hash__ = None
        self.__bio__ = None

    # Creates a new user, adds it to the database, and returns the resulting user object
    # Throws a NameError if the username already exists
    @staticmethod
    def create(connection, username, password, email=None):
        # check if the username already exists
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = cursor.fetchall()
        if len(result) == 0:
            # insert user information into the database
            date_created = datetime.datetime.now()
            query = "INSERT INTO users (username, email, date_created, password_hash) VALUES (%s, %s, %s, %s) RETURNING id"
            data = (username, email, date_created, password)
            cursor.execute(query, data)
            connection.commit()

            # create a user object from the data
            u = User(cursor.fetchone()[0])
            u.__username__ = username
            u.__email__ = email
            u.__date_created__ = date_created
            u.__password_hash__ = password
            u.connection = connection
            cursor.close()
            return u
        else:
            cursor.close()
            raise NameError("User already exists")

    # Reads a user from the database, either by user id or by username
    @staticmethod
    def read(connection, identifier: int | str):
        # Try to read the data, if it doesn't exist then throw a NameError.
        try:
            # If a username instead of user id was provided, find the corresponding user id
            if type(identifier) == str:
                cursor = connection.cursor()
                cursor.execute("SELECT id FROM users WHERE username = %s", (identifier,))
                user_id = cursor.fetchone()[0]
            elif type(identifier) == int:
                user_id = identifier
            else:
                raise TypeError(f"User ID or username expected, got {type(identifier)} instead.")

            u = User(user_id)
            u.connection = connection
            u.update_values()
            return u

        except NameError:
            raise NameError("User not found")
        except TypeError:
            raise NameError("User not found")

    # --- GETTERS AND SETTERS ----
    # When a User object's atomic properties (username, email, date created, etc.) are called, a getter function retrieves them from its private field.
    # When an atomic value is modified, the change is sent to the database with a setter function.
    # There are also getters that query the database for list objects (posts, followers, etc.) but no setters, as these are read-only.

    @property
    def username(self):
        return self.__username__

    # The username field gets special treatment for its setter, as username is a primary key and thus cannot have a duplicate.
    @username.setter
    def username(self, username: str):
        # check if the username already exists
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = cursor.fetchall()

        if len(result) == 0:
            # modify username
            cursor.execute("UPDATE users set username = %s where id = %s", (username, self.user_id))
            self.__username__ = username
            cursor.close()
        else:
            cursor.close()
            raise NameError("User already exists")

    @property
    def email(self):
        return self.__email__

    @email.setter
    def email(self, email: str):
        # modify email
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set email = %s where id = %s", (email, self.user_id))
        self.__email__ = email
        cursor.close()

    @property
    def date_created(self):
        return self.__date_created__

    @date_created.setter
    def date_created(self, date_created: datetime.datetime):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set date_created = %s where id = %s", (date_created, self.user_id))
        self.__date_created__ = date_created
        cursor.close()

    @property
    def password_hash(self):
        return self.__password_hash__

    @password_hash.setter
    def password_hash(self, password_hash: str):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set password_hash = %s where id = %s", (password_hash, self.user_id))
        self.__password_hash__ = password_hash
        cursor.close()

    @property
    def bio(self):
        return self.__bio__

    @bio.setter
    def bio(self, bio: str):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set bio = %s where id = %s", (bio, self.user_id))
        self.__bio__ = bio
        cursor.close()

    @property
    def url(self):
        return routes["user"].format(self.username)

    # Gets the user's posts from the database, returning a list of Post objects
    @property
    def posts(self):
        # query a list of post ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM posts WHERE author = %s ORDER BY date_posted DESC", (self.user_id,))
        result = cursor.fetchall()

        # convert to post objects
        posts = []
        for post_id in result:
            posts.append(Post.read(self.connection, post_id[0]))
        return posts

    # Gets the user's liked posts from the database, returning a list of Post objects
    @property
    def liked_posts(self):
        # query a list of post ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT liked FROM likes WHERE liker = %s ORDER BY date_liked DESC", (self.user_id,))
        result = cursor.fetchall()

        # convert to post objects
        posts = []
        for post_id in result:
            try:
                posts.append(Post.read(self.connection, post_id[0]))
            except NameError:
                self.unlike(post_id)
        return posts

    # Gets the user's followers, returning a list of User objects
    @property
    def followers(self):
        # query a list of user ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM follows WHERE following = %s ORDER BY date_followed DESC", (self.user_id,))
        result = cursor.fetchall()

        # convert to user objects
        users = []
        for user_id in result:
            users.append(User.read(self.connection, user_id))
        return users

    # Gets a list of the user's followers ids (for when the user objects are unnecessary)
    @property
    def follower_ids(self):
        # query a list of user ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM follows WHERE following = %s ORDER BY date_followed DESC", (self.user_id,))
        result = cursor.fetchall()
        return result

    # Gets the user's followed users, returning a list of User objects
    @property
    def following(self):
        # query a list of user ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM follows WHERE follower = %s ORDER BY date_followed DESC", (self.user_id,))
        result = cursor.fetchall()

        # convert to user objects
        users = []
        for user_id in result:
            users.append(User.read(self.connection, user_id))
        return users

    # Updates the atomic values stored in the User
    def update_values(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (self.user_id,))
        result = cursor.fetchall()[0]
        self.__username__ = result[1]
        self.__email__ = result[2]
        self.__date_created__ = result[3]
        self.__password_hash__ = result[4]
        self.__bio__ = result[5]

    # --- USER-SPECIFIC METHODS ---
    # These are various user-specific actions one can perform.

    def is_liked(self, post_id: int):
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT id from likes WHERE liker = %s AND liked = %s", (self.user_id, post_id))
            result = cursor.fetchall()
            cursor.close()
            return len(result) > 0
        except Exception:
            return False

    def is_followed(self, user_id: int):
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT id from follows WHERE follower = %s AND following = %s", (self.user_id, user_id))
            result = cursor.fetchall()
            cursor.close()
            return len(result) > 0
        except Exception:
            return False


    # Make the user follow another user
    def follow(self, user_id: int):
        cursor = self.connection.cursor()
        # check if the user to follow exists
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchall()
        if len(result) != 0:
            # check to make sure user hasn't been followed yet
            if not self.is_followed(user_id):
                # add the follower relationship to the database
                date_followed = datetime.datetime.now()
                cursor.execute("INSERT INTO follows (follower, following, date_followed) VALUES (%s, %s, %s) ", (self.user_id, user_id, date_followed))
                self.connection.commit()
                cursor.close()
            else:
                cursor.close()
                raise NameError("User already followed")
        else:
            cursor.close()
            raise NameError("User doesn't exist")

    # Make the user unfollow another user
    def unfollow(self, user_id:int):
        cursor = self.connection.cursor()
        try:
            # attempt to remove the follower relationship
            cursor.execute("DELETE FROM follows WHERE follower = %s AND following = %s", (self.user_id, user_id,))
            self.connection.commit()
            cursor.close()
        except NameError:
            cursor.close()
            # Probably makes life harder to throw an error
            # raise NameError("User already unfollowed")


    # Make the user like a post
    def like(self, post_id:int):
        # check if the post to like exists
        cursor = self.connection.cursor()
        if not self.is_liked(post_id):
            # check to make sure the post hasn't been liked yet
            cursor.execute("SELECT id from likes WHERE liker = %s AND liked = %s", (self.user_id, post_id))
            result = cursor.fetchall()
            if len(result) == 0:
                # attempt to add the follower relationship
                date_liked = datetime.datetime.now()
                cursor.execute("INSERT INTO likes (liker, liked, date_liked) VALUES (%s, %s, %s)", (self.user_id, post_id, date_liked))
                self.connection.commit()
                cursor.close()
            else:
                cursor.close()
                raise NameError("Post already liked")
        else:
            cursor.close()
            raise NameError("User doesn't exist")

    # Make the user unlike a post
    def unlike(self, post_id:int):
        cursor = self.connection.cursor()
        try:
            # attempt to remove the follower relationship
            cursor.execute("DELETE FROM likes WHERE liker = %s AND liked = %s", (self.user_id, post_id))
            self.connection.commit()
            cursor.close()
        except NameError:
            cursor.close()
            # Probably makes life harder to throw an error
            # raise NameError("Post already unliked")

