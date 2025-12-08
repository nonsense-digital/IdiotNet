from flask import Blueprint, render_template, abort, request, redirect
from helpers.auth import *
from helpers.db import *
from helpers.listings import paged_posts
from models.post import Post, check_empty
from routes import routes, API

posts = Blueprint('posts', __name__, template_folder='../templates')

@posts.route(routes["post"].format("<int:post_id>"))
def post(post_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    try:
        read_post = Post.read(connection, post_id)
        return render_template('posts/post.html', routes=routes, user=local_user, post=read_post, API=API)
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] Post {post_id} not found.")
        abort(404, "Post not found")

@posts.route(routes["latest"])
def latest():
    sort_by = request.args.get("sort_by")
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    posts, is_last_page = paged_posts(page, sort_by=sort_by)
    return render_template('posts/latest.html', routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page)



@posts.route(routes["new_post"], methods=['GET', 'POST'])
def new_post():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)

    if not local_user:

        return redirect(routes["login"])
    else:
        if request.method == 'GET':
            return render_template("posts/new.html", routes=routes, user=local_user)
        else:
            title = request.form.get('title')
            content = request.form.get('content')

            if check_empty(title):
                return render_template("posts/new.html", routes=routes, user=local_user, error_message="Title cannot be blank")
            elif check_empty(content):
                return render_template("posts/new.html", routes=routes, user=local_user, error_message="Content cannot be blank")

            staged_post = Post.publish(connection, title, content, local_user.user_id)
            current_app.logger.info(f"[IP {request.remote_addr}] {local_user.username} created post {staged_post.post_id}")
            return redirect(staged_post.url)

@posts.route(routes["post_edit"].format("<post_id>"), methods=['GET', 'POST'])
def edit_post(post_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)

    if not local_user:
        return redirect(routes["login"])
    else:
        read_post = Post.read(connection, post_id)

        if read_post.author.user_id == local_user.user_id:
            if request.method == 'GET':
                return render_template("posts/edit.html", routes=routes, user=local_user, post=read_post)
            else:
                title = request.form.get('title')
                content = request.form.get('content')

                if check_empty(title):
                    return render_template("posts/new.html", routes=routes, user=local_user,
                                           error_message="Title cannot be blank")
                elif check_empty(content):
                    return render_template("posts/new.html", routes=routes, user=local_user,
                                           error_message="Content cannot be blank")

                read_post.title = title
                read_post.content = content
                read_post.date_modified = datetime.datetime.now()
                current_app.logger.info(f"[IP {request.remote_addr}] {local_user.username} edited post {read_post.post_id}")
                return redirect(read_post.url)
        else:

            return redirect(routes["post"].format(post_id))

