from datetime import datetime
from pathlib import Path
import procrastinate
import os, helpers.db
from jinja2 import Environment, FileSystemLoader

from helpers import db
from helpers.misc import get_mentions
from models.comment import Comment
from models.notification import MessageType, Notification
from models.permissions import PunishmentType, CensorType
from models.post import Post
from models.user import User

# DO NOT PASS WEIRD OBJECTS INTO THE FUNCTIONS THAT START WITH @app_queue.task
# THESE FUNCTIONS ARE SPECIAL SCHEDULED JOBS THAT ONLY ACCEPT NORMAL PARAMETER SUCH AS NUMBERS, STRINGS, ENUMS
# IF YOU WANT AN OBJECT, PASS THE OBJECT'S ID INSTEAD

# init the whole thing
connector = procrastinate.PsycopgConnector(
            kwargs={
                "dbname": os.getenv("DB_NAME"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "host": os.getenv("DB_HOST"),
                "port": os.getenv("DB_PORT"),
                "sslmode": os.getenv("DB_SSL_MODE")
            }
        )
app_queue = procrastinate.App(connector=connector)

# set up the schema
def init_schema():
    with app_queue.open() as app:
        try:
            if not app.check_connection():
                app.schema_manager.apply_schema()
        except Exception as exc:
            # Print the original database exception underneath Procrastinate's wrapper
            if hasattr(exc, '__cause__') and exc.__cause__:
                print("--- SCHEMA UPDATE EXCEPTION ---")
                print(exc.__cause__)
            raise exc

# Notifies a user when followed by another user
@app_queue.task(queue='notifications')
def follow(followed_id:int, follower_id:int):
    with db.get_db_connection(use_g=False) as connection:
        followed = User.read(connection, followed_id)
        follower = User.read(connection, follower_id)
        content = get_template(MessageType.FOLLOW).render(follower=follower)
        Notification.send(connection, MessageType.FOLLOW, content, followed.user_id)

# Notifies a user when their post was liked by another user
@app_queue.task(queue='notifications')
def like(liked_id:int, liker_id:int):
    with db.get_db_connection(use_g=False) as connection:
        liked = Post.read(connection, liked_id)
        liker = User.read(connection, liker_id)
        content = get_template(MessageType.LIKE).render(liked=liked, liker=liker)
        Notification.send(connection, MessageType.LIKE, content, liked.author.user_id)

# Notifies a user when another user comments on their post
@app_queue.task(queue='notifications')
def post_comment(post_id:int, comment_id:int, commenter_id:int):
    with db.get_db_connection(use_g=False) as connection:
        # get a bunch of stuff from ids
        post = Post.read(connection, post_id)
        comment = Comment.read(connection, comment_id)
        commenter = User.read(connection, commenter_id)
        content = get_template(MessageType.POST_COMMENT).render(post=post, comment=comment, commenter=commenter)
        Notification.send(connection, MessageType.POST_COMMENT, content, post.author.user_id)

# Notifies the OP (original poster) and OC (original commenter) of a comment thread
# Might get slow for large comment threads
@app_queue.task(queue='notifications')
def comment_reply(post_id:int, root_id:int, reply_id:int, replier_id:int):
    with (db.get_db_connection(use_g=False) as connection):
        # get a bunch of stuff from ids
        post = Post.read(connection, post_id)
        root = Comment.read(connection, root_id)
        reply = Comment.read(connection, reply_id)
        replier = User.read(connection, replier_id)

        content = get_template(MessageType.COMMENT_REPLY).render(reply=reply, replier=replier)


        # notify the OP using the post_comment one
        if post.author.user_id != replier_id:
            post_comment(post_id=post_id, comment_id=reply_id, commenter_id=replier.user_id)

        # notify the OC
        if root.author.user_id != replier_id and root.author.user_id != post.author.user_id:
            Notification.send(connection, MessageType.COMMENT_REPLY, content, root.author.user_id)

        # notify all other commenters in the thread
        already_sent = set()
        for other_reply in root.replies:
            author_id = other_reply.author.author_id
            if author_id not in already_sent and author_id != post.author.user_id and author_id != root.author.user_id and author_id != replier_id:
                Notification.send(connection, MessageType.COMMENT_REPLY, content, author_id)
                already_sent.add(author_id)



# 2 possible paths (edit, comment)
# Be careful with this guy, it can notify as many users as there are watching a post
# hopefully nothing bad happens......
# watched_id = post id
# commenter_id is used to prevent someone from getting notified about their own comment
@app_queue.task(queue='notifications')
def watched_post(watched_id:int, commenter_id=-1):
    with db.get_db_connection(use_g=False) as connection:
        watched = Post.read(connection, watched_id)
        content = get_template(MessageType.WATCHED_POST).render(watched=watched)
        watchers = watched.watchers
        for watcher in watchers:
            if watcher.user_id != commenter_id: # don't notify for own comments
                Notification.send(connection, MessageType.WATCHED_POST, content, watcher.user_id)

# mentioner_id = user id (sender)
# mentioned user is determined from a regex search in the content
# mention_id = post/comment id
@app_queue.task(queue='notifications')
def mention(mentioner_id:int, mention_id:int, is_comment:bool):
    with db.get_db_connection(use_g=False) as connection:
        mentioner = User.read(connection, mentioner_id)
        try:
            mention = Comment.read(connection, mention_id) if is_comment else Post.read(connection, mention_id)
        except NameError:
            return # an ID mismatch may have happened, let's just ignore this deferred task
        mentioned_usernames = get_mentions(mention.content)
        content = get_template(MessageType.MENTION).render(mentioner=mentioner, mention=mention, is_comment=is_comment)
        # only send to users that actually exist
        for mentioned_username in mentioned_usernames:
            try:
                mentioned_id = User.read(connection, mentioned_username).user_id
                if mentioned_id != mentioner_id: # don't notify self-mentions
                    Notification.send(connection, MessageType.MENTION, content, mentioned_id)
            except NameError:
                pass

# this is only used for muting, because you get a huge message already for bans/permabans
@app_queue.task(queue='notifications')
def admin_punishment(target_id:int):
    with db.get_db_connection(use_g=False) as connection:
        target = User.read(connection, target_id)
        content = get_template(MessageType.ADMIN).render(target=target, is_mute=True)
        Notification.send(connection, MessageType.ADMIN, content, target_id)

# 3 possible paths (post, comment, bio)
@app_queue.task(queue='notifications')
def admin_censor(target_id:int, censor_type:str, censored:str=""):
    # we use a string for the post title because it was already deleted
    # or, we use a string for comment content
    # or, we leave it empty for a bio
    with db.get_db_connection(use_g=False) as connection:
        content = get_template(MessageType.ADMIN).render(censor_type=censor_type, censored=censored, is_mute=False)
        Notification.send(connection, MessageType.ADMIN, content, target_id)

@app_queue.task(queue='notifications')
def admin_role_change(target_id:int, role:str):
    with db.get_db_connection(use_g=False) as connection:
        content = get_template(MessageType.ADMIN).render(role=role)
        Notification.send(connection, MessageType.ADMIN, content, target_id)

@app_queue.task(queue='notifications')
def admin_post_approve(title:str, url:str, author_id:int, approved:bool):
    with db.get_db_connection(use_g=False) as connection:
        content = get_template(MessageType.ADMIN).render(title=title, url=url, approved=approved)
        Notification.send(connection, MessageType.ADMIN, content, author_id)


# hehehehe I wonder what this could be for
@app_queue.task(queue='notifications')
def custom(user_id:int, content:str):
    with db.get_db_connection(use_g=False) as connection:
        Notification.send(connection, MessageType.CUSTOM, content, user_id)

# get a template to format for notifications
def get_template(message_type:MessageType):
    current_file = Path(__file__).resolve()  # get current file
    template_dir = current_file.parent.parent / "templates" / "notifications"  # get template directory
    env = Environment(loader=FileSystemLoader(str(template_dir)))  # get jinja env
    template = env.get_template(f'{message_type.value}.html')
    return template