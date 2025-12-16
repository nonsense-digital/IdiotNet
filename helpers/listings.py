from helpers.db import *
from models.post import Post, SortMethod
from enum import Enum

from models.user import User


class SearchType(Enum):
    ALL_POSTS = 0
    USER_POSTS = 1
    USER_LIKED_POSTS = 2
    QUERY = 3

'''    if search_user is None:
        posts = Post.latest(connection, count, offset*count, SortMethod.LATEST)
    else:
        if search_type == "liked":
            posts = search_user.liked_posts[offset*count:offset*count+count]
        elif search_type == "latest":
            posts = search_user.posts[offset*count:offset*count+count]
        else:
            raise TypeError("Invalid search type")'''


def search_posts(count:int, offset:int=0, search_user:User=None, search_type:SearchType="latest", query:str="") -> tuple:
    connection = get_db_connection()
    posts = ()
    match search_type:
        case SearchType.ALL_POSTS:
            posts = Post.latest(connection, count, offset * count, SortMethod.LATEST)
        case SearchType.USER_POSTS:
            posts = search_user.posts[offset * count:offset * count + count]
        case SearchType.USER_LIKED_POSTS:
            posts = search_user.liked_posts[offset * count:offset * count + count]
        case SearchType.QUERY:
            print(count, offset)
            posts = Post.search(connection, query, count, offset * count)
        case _:
            raise TypeError("Invalid search type")
    return posts

def paged_posts(page:int, **filters) -> tuple:
    print(page)
    posts = search_posts(20, page - 1, **filters)
    is_last_page = len(posts) < 20
    return posts, is_last_page