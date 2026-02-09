from flask import Blueprint, render_template, abort, request, redirect, send_file
from helpers.auth import *
from helpers.db import *
from helpers.listings import paged_posts, SearchType
from models.client import Client
from models.permissions import PunishmentType, Role
from models.post import Post, check_empty
from routes import routes, API
from models.image import Image

posts = Blueprint('posts', __name__, template_folder='../templates')

# view a user-generated post, with a title, content, images, comments, and additional options for OP and admins
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

# a list of the latest posts
@posts.route(routes["latest"])
def latest():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    posts, is_last_page = paged_posts(page, search_type=SearchType.ALL)
    return render_template('posts/latest.html', routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page)

# menu to create a new post with title, content, and images
@posts.route(routes["new_post"], methods=['GET', 'POST'])
def new_post():
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    post_images = []
    client = Client(connection, request.remote_addr)

    if not local_user:

        return redirect(routes["login"])
    else:
        if request.method == 'GET':
            return render_template("posts/new.html", routes=routes, user=local_user, client=client)
        else:
            # only allow posting if the user isn't muted
            if local_user.punishment_status != PunishmentType.MUTE and client.punishment_status != PunishmentType.MUTE:
                # get text info from POST request
                title = request.form.get('title')
                content = request.form.get('content')
                
                # check for empty content
                if check_empty(title):
                    return render_template("posts/new.html", routes=routes, user=local_user, error_message="Title cannot be blank", client=client)
                elif check_empty(content):
                    return render_template("posts/new.html", routes=routes, user=local_user, error_message="Content cannot be blank", client=client)
                force_approve = (local_user.role != Role.MEMBER) # posts from moderators and admins don't need approval
                staged_post = Post.publish(connection, title, content, local_user.user_id, force_approve=force_approve)
                
                # now that the post object exists, add the relevant info to each image
                images = request.files.getlist('file')
                if str(images) != "[<FileStorage: '' ('application/octet-stream')>]": #this is what python printed when I asked don't question it
                    for file in images:
                        Image.create(connection, file, local_user.user_id, staged_post.post_id)
                current_app.logger.info(f"[IP {request.remote_addr}] {local_user.username} created post {staged_post.post_id}")
                return redirect(staged_post.url)
            else:
                return render_template("posts/new.html", routes=routes, user=local_user, client=client)

# display an image attachment
@posts.route(routes["image"].format("<int:image_id>"))
def image(image_id):
    connection = get_db_connection()
    try:
        ext = Image.read(connection, image_id).file_ext
        filename = 'uploads/' + str(image_id) + "." + ext
        return send_file(filename, mimetype='image/'+ext)
    except NameError:
        abort(404, "Image not found")
    except IOError:
        abort(404, "Image not found")

# edit an already-created post
@posts.route(routes["post_edit"].format("<post_id>"), methods=['GET', 'POST'])
def edit_post(post_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    client = Client(connection, request.remote_addr)

    if not local_user:
        return redirect(routes["login"])
    else:
        read_post = Post.read(connection, post_id)

        if read_post.author.user_id == local_user.user_id:
            if request.method == 'GET':
                return render_template("posts/edit.html", routes=routes, user=local_user, post=read_post, client=client)
            else:
                if local_user.punishment_status != PunishmentType.MUTE and client.punishment_status != PunishmentType.MUTE:
                    title = request.form.get('title')
                    content = request.form.get('content')

                    if check_empty(title):
                        return render_template("posts/new.html", routes=routes, user=local_user,
                                               error_message="Title cannot be blank", client=client)
                    elif check_empty(content):
                        return render_template("posts/new.html", routes=routes, user=local_user,
                                               error_message="Content cannot be blank", client=client)

                    read_post.title = title
                    read_post.content = content
                    read_post.date_modified = datetime.datetime.now()
                    current_app.logger.info(f"[IP {request.remote_addr}] {local_user.username} edited post {read_post.post_id}")
                    return redirect(read_post.url)
                else:
                    return render_template("posts/edit.html", routes=routes, user=local_user, post=read_post, client=client)
        else:
            return redirect(routes["post"].format(post_id))


