from flask import Blueprint, redirect, render_template, abort, request
from helpers.auth import *
from helpers.db import *
from helpers.listings import search_posts, SearchType, paged_posts, paged_notifs
from routes import routes

main = Blueprint('index', __name__, template_folder='../templates')

# Main page, displaying a welcome message and some of the latest posts
@main.route(routes["home"])
def index():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    latest_posts = search_posts(10, search_type=SearchType.ALL)
    return render_template('index.html', routes=routes, user=local_user, latest_posts=latest_posts)

# Simple description of the site and who made it, and some rules
@main.route(routes["about"])
def about():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    return render_template('about.html', routes=routes, user=local_user)

# post search function, accessible from the search bar on top
@main.route(routes["search"])
def search():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    if "query" in request.args:
        query = request.args["query"]
        if "page" in request.args:
            page = int(request.args["page"])
        else:
            page = 1
        results, is_last_page = paged_posts(page, search_type=SearchType.QUERY, query=query)
        return render_template('search.html', routes=routes, user=local_user, posts=results, page=page, query=query, is_last_page=is_last_page)
    else:
        return render_template("search.html", routes=routes, user=local_user)

# big notifications menu with multiple pages
@main.route(routes["notifs"])
def notifs():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    if local_user:
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        notifs, is_last_page = paged_notifs(local_user.user_id, page)
        return render_template('notifs.html', routes=routes, user=local_user, notifs=notifs, pagify=True, is_last_page=is_last_page, page=page)
    else:
        return redirect(routes["login"])

