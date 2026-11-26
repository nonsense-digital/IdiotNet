from datetime import datetime
from enum import Enum

from flask import current_app

class MessageType(Enum):
    FOLLOW = 'follow'
    LIKE = 'like'
    POST_COMMENT = 'post_comment'
    COMMENT_REPLY = 'comment_reply'
    WATCHED_POST = 'watched_post'
    MENTION = 'mention'
    ADMIN = 'admin'
    CUSTOM = 'custom'

# notification objects are immutable, and the only action that can be performed is reading or deleting it
class Notification:
    # Initiates an empty notification object. Don't use this! Instead, use one of the type-specific methods
    def __init__(self, message_id:int):
        self.__message_id__ = message_id
        self.__message_type__ = None
        self.__message__ = None
        self.__user_id__ = None
        self.__date_sent__ = None

    # Creates a customized notification object in the database. Don't use this directly! Instead, use the helper functions in notifier.py
    # For optimization purposes, no object is returned
    @staticmethod
    def send(connection, message_type:MessageType, message:str, user_id:int):
        with connection.cursor() as cursor:
            date_sent = datetime.now()
            query = "INSERT INTO notifications (message_type, message, user_id, date_sent) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (message_type.value, message, user_id, date_sent))
            cursor.close()

    @staticmethod
    def read(connection, notification_id:int):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM notifications WHERE id=%s", (notification_id))
            data = cursor.fetchone()
            n = Notification(notification_id)
            n.__message_type__ = data[1]
            n.__message__ = data[2]
            n.__user_id__ = data[3]
            n.__date_sent__ = data[4]
            return n

    # finds a list of all notifications, sorted by date sent
    @staticmethod
    def latest(connection, search_id:int, count: int, offset: int = 0):
        with connection.cursor() as cursor:
            query = "SELECT id FROM notifications WHERE user_id=%s ORDER BY date_sent DESC, id DESC OFFSET %s LIMIT %s"
            cursor.execute(query, (search_id, offset, count))
            data = cursor.fetchall()
            notifs = []
            for record in data:
                n = Notification.read(connection, record)
                notifs.append(n)
            return notifs

    # ugh im so tired of getters and setters and getters and setters
    @property
    def message_id(self):
        return self.__message_id__

    @property
    def message_type(self):
        return self.__message_type__

    @property
    def message(self):
        return self.__message__

    @property
    def user_id(self):
        return self.__user_id__

    @property
    def date_sent(self):
        return self.__date_sent__