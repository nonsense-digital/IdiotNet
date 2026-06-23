from datetime import datetime
from enum import Enum


class MessageType(Enum):
    FOLLOW = 'follow'
    LIKE = 'like'
    POST_COMMENT = 'post_comment'
    COMMENT_REPLY = 'comment_reply'
    WATCHED_POST = 'watched_post'
    MENTION = 'mention'
    ADMIN = 'admin'
    CUSTOM = 'custom'

'''
class Notification:
    # Initiates an empty notification object. Don't use this! Instead, use one of the type-specific methods
    def __init__(self):
        self.__message_type__ = None
        self.__message__ = None
        self.__user_id__ = None
        self.__date_sent__ = None

    # Creates a customized notification object in the database. Don't use this directly! Instead, use one of the type-specific methods
    @staticmethod
    def create(self, message_type:MessageType, message:str, user_id:int, date_sent:datetime):
        self.__message_type__ = message_type
'''