from helpers.db import *
from models.post import Post, SortMethod

def latest_posts(count:int, offset=0, **filters) -> tuple:
    connection = get_db_connection()
    if not "search_user" in filters:
        posts = Post.latest(connection, count, offset*count, SortMethod.LATEST)
    else:
        if "search_type" not in filters:
            filters["search_type"] = "latest"
        if filters["search_type"] == "liked":
            posts = filters["search_user"].liked_posts[offset*count:offset*count+count]
        elif filters["search_type"] == "latest":
            posts = filters["search_user"].posts[offset*count:offset*count+count]
        else:
            raise TypeError("Invalid search type")

    return posts

def paged_posts(page:int, **filters) -> tuple:
    posts = latest_posts(20, page - 1, **filters)
    is_last_page = len(posts) < 20
    return posts, is_last_page