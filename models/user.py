from __future__ import annotations

import datetime
from models.post import Post
from routes import routes
from enum import Enum
from models.permissions import PunishmentType, Role
from models.comment import Comment

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


def check_password(password: str, verify_password: str):
    # Checks a password to make sure it has the correct format, matches the verify password, and is not the same as the previous_password (if specified)
    if password == "":
        return "Password is required"
    elif len(password) > 50:
        return "Password limit is 50 characters"
    elif verify_password != password:
        return "Passwords do not match"
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
        self.__role__ = None
        self.__punishment_status__ = None
        self.__punishment_expiration__ = None
        self.__punishment_reason__ = None

    # Creates a new user, adds it to the database, and returns the resulting user object
    # Throws a NameError if the username already exists
    @staticmethod
    def create(connection, username, password_hash, email=None):
        # check if the username already exists
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = cursor.fetchall()
        if len(result) == 0:
            # insert user information into the database
            date_created = datetime.datetime.now()
            query = "INSERT INTO users (username, email, date_created, password_hash) VALUES (%s, %s, %s, %s) RETURNING id"
            data = (username, email, date_created, password_hash)
            cursor.execute(query, data)
            connection.commit()

            # create a user object from the data
            u = User(cursor.fetchone()[0])
            u.__username__ = username
            u.__email__ = email
            u.__date_created__ = date_created
            u.__password_hash__ = password_hash
            u.__bio__ = ""
            u.__role__ = Role.MEMBER
            u.__punishment_status__ = PunishmentType.NONE
            u.__punishment_expiration__ = None
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
                user_id = User.get_user_id(connection, identifier)
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

    # finds a list of all users, sorted by date created
    @staticmethod
    def latest(connection, count: int, offset: int = 0):
        cursor = connection.cursor()
        query = "SELECT id FROM users ORDER BY date_created DESC OFFSET %s LIMIT %s"
        cursor.execute(query, (offset, count))
        data = cursor.fetchall()
        clients = []
        for record in data:
            p = User.read(connection, record[0])
            clients.append(p)
        return clients

    # finds a list of all punished users, sorted by punishment expiration
    @staticmethod
    def punished(connection, count: int, offset: int = 0):
        cursor = connection.cursor()
        query = "SELECT id FROM users WHERE punishment_status != 'none' ORDER BY punishment_expiration DESC OFFSET %s LIMIT %s"
        cursor.execute(query, (offset, count))
        data = cursor.fetchall()
        users = []
        for record in data:
            p = User.read(connection, record[0])
            users.append(p)
        return users



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
            self.connection.commit()
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
        self.connection.commit()
        self.__email__ = email
        cursor.close()

    @property
    def date_created(self):
        return self.__date_created__

    @date_created.setter
    def date_created(self, date_created: datetime.datetime):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set date_created = %s where id = %s", (date_created, self.user_id))
        self.connection.commit()
        self.__date_created__ = date_created
        cursor.close()

    @property
    def password_hash(self):
        return self.__password_hash__

    @password_hash.setter
    def password_hash(self, password_hash: str):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set password_hash = %s where id = %s", (password_hash, self.user_id))
        self.connection.commit()
        self.__password_hash__ = password_hash
        cursor.close()

    @property
    def bio(self):
        return self.__bio__

    @bio.setter
    def bio(self, bio: str):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set bio = %s where id = %s", (bio, self.user_id))
        self.connection.commit()
        self.__bio__ = bio
        cursor.close()

    @property
    def role(self):
        return self.__role__

    @role.setter
    def role(self, role: Role):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set role = %s where id = %s", (role.value, self.user_id))
        self.connection.commit()
        self.__role__ = role
        cursor.close()

    @property
    def url(self):
        return routes["user"].format(self.username)

    @property
    def punishment_status(self):
        return self.__punishment_status__
    @punishment_status.setter
    def punishment_status(self, punishment_status:PunishmentType):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set punishment_status = %s where id = %s", (punishment_status.value, self.user_id))
        self.connection.commit()
        self.__punishment_status__ = punishment_status
        cursor.close()

    @property
    def punishment_expiration(self):
        return self.__punishment_expiration__
    @punishment_expiration.setter
    def punishment_expiration(self, punishment_expiration: datetime.datetime):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set punishment_expiration = %s where id = %s", (punishment_expiration, self.user_id))
        self.connection.commit()
        self.__punishment_expiration__ = punishment_expiration
        cursor.close()

    @property
    def punishment_reason(self) -> str:
        return self.__punishment_reason__

    @punishment_reason.setter
    def punishment_reason(self, punishment_reason: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute("UPDATE users set punishment_reason = %s where id = %s",
                       (punishment_reason, self.user_id))
        self.connection.commit()
        self.__punishment_reason__ = punishment_reason
        cursor.close()

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

    # Gets the user's post ids from the database (for when the post objects are unnecessary)
    @property
    def post_ids(self):
        # query a list of post ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM posts WHERE author = %s ORDER BY date_posted DESC", (self.user_id,))
        result = [x[0] for x in cursor.fetchall()]
        return result

    # Gets the user's posts from the database, returning a list of Post objects
    @property
    def comments(self):
        # query a list of post ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM comments WHERE author = %s ORDER BY date_posted DESC", (self.user_id,))
        result = cursor.fetchall()

        # convert to post objects
        comments = []
        for post_id in result:
            comments.append(Comment.read(self.connection, post_id[0]))
        return comments

    # Gets the user's post ids from the database (for when the post objects are unnecessary)
    @property
    def comment_ids(self):
        # query a list of post ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM comments WHERE author = %s ORDER BY date_posted DESC", (self.user_id,))
        result = [x[0] for x in cursor.fetchall()]
        return result

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

    # Gets the user's liked post ids from the database (for when the post objects are unnecessary)
    @property
    def liked_post_ids(self):
        # query a list of post ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT liked FROM likes WHERE liker = %s ORDER BY date_liked DESC", (self.user_id,))
        post_ids = [x[0] for x in cursor.fetchall()]
        return post_ids

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
            users.append(User.read(self.connection, user_id[0]))
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
    def following(self) -> list[User]:
        # query a list of user ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM follows WHERE follower = %s ORDER BY date_followed DESC", (self.user_id,))
        result = cursor.fetchall()

        # convert to user objects
        users = []
        for user_id in result:
            users.append(User.read(self.connection, user_id))
        return users

    # Gets a list of the user's followed user ids (for when the user objects are unnecessary)
    @property
    def following_ids(self) -> list[int]:
        # query a list of user ids
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM follows WHERE follower = %s ORDER BY date_followed DESC", (self.user_id,))
        result = cursor.fetchall()
        return result

    # method that gets all active auth tokens (sessions) on the user
    @property
    def tokens(self):
        from models.auth_token import Token
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM tokens WHERE user_id = %s ", (self.user_id,))
        result = cursor.fetchall()
        tokens = []
        for token in result:
            tokens.append(Token.read(self.connection, token[0]))
        return tokens

    # method that gets the ids of all active auth tokens (sessions) on the client
    @property
    def token_ids(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM tokens WHERE user_id = %s", (self.user_id,))
        return [x[0] for x in cursor.fetchall()]

    # Updates the atomic values stored in the User
    def update_values(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (self.user_id,))
        result = cursor.fetchall()
        if len(result) > 0:
            data = result[0]
            self.__username__ = data[1]
            self.__email__ = data[2]
            self.__date_created__ = data[3]
            self.__password_hash__ = data[4]
            self.__bio__ = data[5]
            self.__role__ = Role(data[6])
            self.__punishment_status__ = PunishmentType(data[7])
            self.__punishment_expiration__ = data[8]
            self.__punishment_reason__ = data[9]
        else:
            raise NameError("User does not exist")

    # --- USER-SPECIFIC METHODS ---
    # These are various user-specific actions one can perform.

    # delete all user-generated data
    # used in a permaban
    def clear_data(self):
        # delete all posts
        for post in self.posts:
            post.delete()

        # clear bio
        self.bio = ""

        # remove followed
        for followed in self.following_ids:
            self.unfollow(followed)

        # remove followers
        for follower in self.followers:
            follower.unfollow(self.user_id)

        # remove likes
        for like in self.liked_post_ids:
            self.unlike(like)

        # remove all comments
        for comment in self.comments:
            comment.delete()

    # check if the user has an active punishment
    def check_punishment(self, refresh:bool=False) -> PunishmentType:
        # refresh values if requested
        if refresh:
            self.update_values()

        # check if punishment has expired, if so then reset the punishment
        # (this doesn't apply to permabans, which are irreversible)
        if self.__punishment_expiration__ < datetime.datetime.now() and self.__punishment_status__ != PunishmentType.PERMABAN:
            self.punishment_status = PunishmentType.NONE

        # return punishment status (if any)
        return self.__punishment_status__


    # check if a post has been liked by the user
    def is_liked(self, post_id: int) -> bool:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT id from likes WHERE liker = %s AND liked = %s", (self.user_id, post_id))
            result = cursor.fetchall()
            cursor.close()
            return len(result) > 0
        except Exception:
            return False

    def is_followed(self, user_id: int) -> bool:
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT id from follows WHERE follower = %s AND following = %s", (self.user_id, user_id))
            result = cursor.fetchall()
            cursor.close()
            return len(result) > 0
        except Exception:
            return False


    # Make the user follow another user
    def follow(self, user_id: int) -> None:
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
    def unfollow(self, user_id:int) -> None:
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
    def like(self, post_id:int) -> None:
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
    def unlike(self, post_id:int) -> None:
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

    # helper function to get a user id without pulling all user data
    @staticmethod
    def get_user_id(connection, username:str) -> int:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]
        cursor.close()
        return user_id