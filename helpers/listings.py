from helpers.db import *
from models.client import Client
from models.post import Post, SortMethod
from enum import Enum

from models.user import User


class SearchType(Enum):
    ALL = 0
    USER_POSTS = 1
    USER_LIKED_POSTS = 2
    QUERY = 3
    PUNISHED_ENTITIES = 4

'''    if search_user is None:
        posts = Post.latest(connection, count, offset*count, SortMethod.LATEST)
    else:
        if search_type == "liked":
            posts = search_user.liked_posts[offset*count:offset*count+count]
        elif search_type == "latest":
            posts = search_user.posts[offset*count:offset*count+count]
        else:
            raise TypeError("Invalid search type")'''


def search_posts(count:int, offset:int=0, search_user:User=None, search_type:SearchType=SearchType.ALL, query:str= "") -> tuple:
    connection = get_db_connection()
    posts = ()
    match search_type:
        case SearchType.ALL:
            posts = Post.latest(connection, count, offset * count, SortMethod.LATEST)
        case SearchType.USER_POSTS:
            posts = search_user.posts[offset * count:offset * count + count]
        case SearchType.USER_LIKED_POSTS:
            posts = search_user.liked_posts[offset * count:offset * count + count]
        case SearchType.QUERY:
            posts = Post.search(connection, query, count, offset * count)
        case _:
            raise TypeError("Invalid search type")
    return posts

def paged_posts(page:int, **filters) -> tuple:
    posts = search_posts(20, page - 1, **filters)
    is_last_page = len(posts) < 20
    return posts, is_last_page

def search_clients(count:int, offset:int=0, search_type:SearchType=SearchType.ALL, query:str= "") -> tuple:
    connection = get_db_connection()
    clients = ()
    match search_type:
        case SearchType.ALL:
            clients = Client.latest(connection, count, offset * count)
        case SearchType.PUNISHED_ENTITIES:
            clients = Client.punished(connection, count, offset * count)
        case SearchType.QUERY:
            raise NotImplementedError("Search type not implemented yet.")
        case _:
            raise TypeError("Invalid search type")
    return clients

def paged_clients(page:int, **filters) -> tuple:
    clients = search_clients(20, page - 1, **filters)
    is_last_page = len(clients) < 20
    return clients, is_last_page

def search_users(count:int, offset:int=0, search_type:SearchType=SearchType.ALL, query:str= "") -> tuple:
    connection = get_db_connection()
    users = ()
    match search_type:
        case SearchType.ALL:
            users = User.latest(connection, count, offset * count)
        case SearchType.PUNISHED_ENTITIES:
            users = User.punished(connection, count, offset * count)
        case SearchType.QUERY:
            raise NotImplementedError("Search type not implemented yet.")
        case _:
            raise TypeError("Invalid search type")
    return users

def paged_users(page:int, **filters) -> tuple:
    users = search_users(20, page - 1, **filters)
    is_last_page = len(users) < 20
    return users, is_last_page

def search_sessions(count:int, offset:int=0, search_user=None, search_client=None) -> tuple:
    if search_user is not None:
        sessions = search_user.tokens[offset * count:offset * count + count]
    elif search_client is not None:
        sessions = search_client.tokens[offset * count:offset * count + count]
    else:
        raise ValueError("No target provided")
    return sessions

def paged_sessions(page:int, **filters) -> tuple:
    sessions = search_sessions(20, page - 1, **filters)
    is_last_page = len(sessions) < 20
    return sessions, is_last_page