import datetime

from post import Post
from routes import routes

class User:
    def __init__(self, username, password, email=None):
        self.username = username
        self.user_id = -1
        self.email = email
        self.password = password
        self.date_created = None
        self.followers = []
        self.following = []
        self.posts = []
        self.liked_posts = []
        self.is_created = False
        self.bio = ""
        self.url = None

    def create(self, connection):
        if not self.is_created:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (self.username,))
            result = cursor.fetchall()
            if len(result) == 0:
                self.is_created = True
                self.date_created = datetime.datetime.now()
                self.url = routes["user"].format(self.username)
                query = "INSERT INTO users (username, email, date_created, password_hash, followers, posts, following, liked_posts, bio) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"
                data = (self.username, self.email, self.date_created, self.password, self.followers, self.posts, self.following,
                        self.liked_posts, self.bio)
                cursor.execute(query, data)
                connection.commit()
                self.user_id = cursor.fetchone()[0]
                cursor.close()
            else:
                cursor.close()
                raise Exception("User already exists")
        else:
            raise Exception('User already exists')

    def follower_count(self):
        return len(self.followers)

    def add_post(self, connection, post_id:int):
        if self.is_created:
            cursor = connection.cursor()
            cursor.execute("SELECT posts FROM users WHERE username = %s", (self.username,))
            data = cursor.fetchone()[0]
            data.append(post_id)
            self.posts = data
            cursor.execute("UPDATE users SET posts = %s WHERE username = %s", (data, self.username))
            connection.commit()
            cursor.close()
        else:
            raise Exception("Cannot add post to nonexistent user")

    def like_post(self, connection, post_id: int, add_like:bool=True):
        if self.is_created:
            cursor = connection.cursor()
            cursor.execute("SELECT liked_posts FROM users WHERE username = %s", (self.username,))
            data = cursor.fetchone()[0]
            if (not post_id in data and add_like) or (post_id in data and not add_like):
                if add_like:
                    data.append(post_id)
                else:
                    data.remove(post_id)
                self.posts = data
                cursor.execute("UPDATE users SET liked_posts = %s WHERE username = %s", (data, self.username))
                connection.commit()
                cursor.close()
            else:
                cursor.close()
                raise ValueError("Operation cannot be done")
        else:
            raise NameError("User doesn't exist")

    def change_password(self, connection, password):
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password, self.user_id,))
        connection.commit()
        cursor.close()
        self.password = password


    def add_follower(self, connection, follower, add_follow:bool=True):
        if self.is_created:
            cursor = connection.cursor()
            cursor.execute("SELECT followers FROM users WHERE id = %s", (self.user_id,))
            follower_data = cursor.fetchone()[0]
            cursor.execute("SELECT following FROM users WHERE id = %s", (follower.user_id,))
            following_data = cursor.fetchone()[0]
            can_set_follower = (not follower.user_id in follower_data and add_follow) or (follower.user_id in follower_data and not add_follow)
            can_set_following = (not follower.user_id in follower_data and add_follow) or (follower.user_id in follower_data and not add_follow)
            if can_set_follower and can_set_following:
                if add_follow:
                    follower_data.append(follower.user_id)
                    following_data.append(self.user_id)
                else:
                    follower_data.remove(follower.user_id)
                    following_data.remove(self.user_id)
                self.followers = follower_data
                cursor.execute("UPDATE users SET followers = %s WHERE id = %s",
                               (follower_data, self.user_id))
                cursor.execute("UPDATE users SET following = %s WHERE id = %s",
                               (following_data, follower.user_id))
                connection.commit()
                cursor.close()
            else:
                cursor.close()
                raise ValueError("Operation cannot be done")
        else:
            raise NameError("User doesn't exist")

    def update_bio(self, connection, bio):
        self.bio = bio
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET bio = %s WHERE id = %s", (bio, self.user_id))
        connection.commit()
        cursor.close()

    def latest(self, connection, count, offset=0):
        posts = []
        deleted = []
        self.posts.sort(reverse=True)
        for post_id in self.posts[offset:offset+count]:
            try:
                posts.append(Post.read(connection, post_id))
            except NameError:
                deleted.append(post_id)
        if len(deleted) > 0:
            self.prune_posts(connection, deleted)
        return posts

    def prune_posts(self, connection, post_ids: list[int], type=0):
        cursor = connection.cursor()
        if type == 0:
            cursor.execute("SELECT posts FROM users WHERE username = %s", (self.username,))
            self.posts = cursor.fetchone()[0]
            main_list = self.posts
        elif type == 1:
            cursor.execute("SELECT liked_posts FROM users WHERE username = %s", (self.username,))
            self.liked_posts = cursor.fetchone()[0]
            main_list = self.liked_posts
        else:
            raise ValueError("Invalid post list type")
        for post_id in post_ids:
            main_list.remove(post_id)
        if type == 0:
            cursor.execute("UPDATE users SET posts = %s WHERE username = %s", (self.posts, self.username))
        elif type == 1:
            cursor.execute("UPDATE users SET liked_posts = %s WHERE username = %s", (self.liked_posts, self.username))
        connection.commit()
        cursor.close()

    def liked(self, connection, count, offset=0):
        posts = []
        try:
            self.liked_posts.sort(reverse=True)
            for post_id in self.liked_posts[offset:offset+count]:
                try:
                    posts.append(Post.read(connection, post_id))
                except NameError:
                    pass
        except AttributeError:
            return []
        return posts

    @staticmethod
    def read(connection, identifier):
        if isinstance(identifier, str):
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (identifier,))
            data = cursor.fetchone()
            if data is None:
                raise NameError("User not found")
            else:
                return User.record_to_object(data)
        elif isinstance(identifier, int):
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (identifier,))
            data = cursor.fetchone()
            if data is None:
                raise NameError("User not found")
            else:
                return User.record_to_object(data)
        else:
            raise ValueError("Invalid identifier")

    @staticmethod
    def record_to_object(record):
        u = User(username=record[1], password=record[4], email=record[2])
        u.user_id = record[0]
        u.date_created = record[3]
        u.followers = record[6]
        u.posts = record[5]
        u.following = record[7]
        u.liked_posts = record[8]
        u.bio = record[9]
        u.is_created = True
        u.url = routes["user"].format(u.username)
        return u