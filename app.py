from flask import Flask, request, render_template, redirect, make_response, abort, jsonify

from comment import Comment
from post import Post, SortMethod
from user import User, check_username, check_password
from routes import routes, API
from auth_token import Token
import os
from dotenv import load_dotenv
import psycopg2

# Set up database connection
load_dotenv()
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
global_connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )

def get_db_connection():
    global global_connection
    return global_connection

# check if DB version is correct
SEVER_VERSION = "1.0"
cursor = global_connection.cursor()
try:
    cursor.execute("SELECT value FROM config WHERE key = 'version'")
    database_version = cursor.fetchone()[0]
    cursor.close()
    if database_version != "1.0":
        cursor.close()
        global_connection.close()
        raise TypeError(f"Expected database version {SEVER_VERSION}, got {database_version} instead.")
except Exception as e:
    cursor.close()
    global_connection.close()
    raise TypeError("Database version not found. This either means your database is older than 1.0, or you deleted the version number in the config table.")


# Set up Flask app
app = Flask(__name__)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    get_db_connection().close()
    func()
    return 'Server shutting down...'

def latest_posts(count:int, offset=0, search_user:User=None, sort_by="latest", filter=None) -> tuple:
    connection = get_db_connection()
    if not search_user:
        posts = Post.latest(connection, count, offset*count, SortMethod.LATEST)
    else:
        if filter == "liked":
            posts = search_user.liked_posts
        else:
            posts = search_user.posts

    return posts

def paged_posts(page:int, search_user:User=None, sort_by="latest", filter=None) -> tuple:
    posts = latest_posts(20, page - 1, search_user, sort_by, filter)
    is_last_page = len(posts) < 20
    return posts, is_last_page

@app.route(routes["home"])
def index():
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    return render_template('index.html', routes=routes, user=local_user, latest_posts=latest_posts)

@app.route(routes["latest"])
def latest():
    sort_by = request.args.get("sort_by")
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    posts, is_last_page = paged_posts(page, sort_by=sort_by)
    return render_template('posts/latest.html', routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page)

@app.route(routes["user"].format("<username>"))
def user(username):
    try:
        connection = get_db_connection()
        local_user = check_token(connection, request.cookies)
        search_user = User.read(connection, username)
        posts_latest = latest_posts(3, 0, search_user)
        posts_liked = latest_posts(3, 0, search_user, filter="liked")
        return render_template('users/user.html', routes=routes, posts_latest=posts_latest, posts_liked=posts_liked, user=local_user, search_user=search_user)
    except NameError:
        abort(404, "User not found")

@app.route(routes["user_posts"].format("<username>"))
def user_posts(username):
    try:
        connection = get_db_connection()
        local_user = check_token(connection, request.cookies)
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        search_user = User.read(connection, username)
        posts, is_last_page = paged_posts(page, search_user)

        return render_template('users/posts.html', type="Posts", routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        abort(404, "User not found")

@app.route(routes["user_liked_posts"].format("<username>"))
def user_liked_posts(username):
    try:
        connection = get_db_connection()
        local_user = check_token(connection, request.cookies)
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        search_user = User.read(connection, username)
        posts, is_last_page = paged_posts(page, search_user, filter="liked")

        return render_template('users/posts.html', type="Liked Posts", routes=routes, user=local_user, posts=posts, is_last_page=is_last_page, page=page, search_user=search_user)
    except NameError:
        abort(404, "User not found")

@app.route(routes["post"].format("<int:post_id>"))
def post(post_id):
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    try:
        read_post = Post.read(connection, post_id)
        return render_template('posts/post.html', routes=routes, user=local_user, post=read_post, API=API)
    except NameError:
        abort(404, "Post not found")

def check_token(connection, cookies):
    if 'token' in cookies:
        try:
            token = Token.read(connection, cookies['token'])
            local_user = User.read(connection, token.user_id)
            return local_user
        except NameError:
            return None
    else:
        #cookies.remove('token')
        return None

@app.route(routes["login"], methods=['GET', 'POST'])
def login():
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)

    if local_user:

        print(f"{local_user.username} is already logged in")
        return redirect(routes["home"])
    else:
        if request.method == 'GET':

            return render_template("users/login.html", routes=routes, user=local_user)
        else:
            username = request.form.get('username')
            password = request.form.get('password')

            try:
                local_user = User.read(connection, username)

                if local_user.password_hash == password:
                    print(f"User {username} logged in successfully")
                    token = Token(local_user.user_id)
                    resp = make_response(redirect(routes["home"]))
                    token.create(connection)

                    resp.set_cookie('token', token.token_id)
                    return resp
                else:
                    print(f"User {username} failed to log in")

                    return render_template("users/login.html", routes=routes, user=local_user, error_message=f'Incorrect password')
            except NameError:
                return render_template("users/login.html", routes=routes, user=local_user, error_message=f'User {username} does not exist')

@app.route(routes["new_post"], methods=['GET', 'POST'])
def new_post():
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)

    if not local_user:

        return redirect(routes["login"])
    else:
        if request.method == 'GET':

            return render_template("posts/new.html", routes=routes, user=local_user)
        else:
            title = request.form.get('title')
            content = request.form.get('content')

            staged_post = Post.publish(connection, title, content, local_user.user_id)
            print(f"{local_user.username} created post #{staged_post.post_id}")
            return redirect(staged_post.url)

@app.route(routes["post_edit"].format("<post_id>"), methods=['GET', 'POST'])
def edit_post(post_id):
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)

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

                read_post.title = title
                read_post.content = content
                print(f"{local_user.username} edited post #{post_id}")
                return redirect(read_post.url)
        else:

            return redirect(routes["post"].format(post_id))

@app.route(routes["user_edit"].format("<username>"), methods=['GET', 'POST'])
def user_edit(username):
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)

    if not local_user:

        return redirect(routes["login"])
    else:
        if request.method == 'GET':

            return render_template("users/edit.html", routes=routes, user=local_user)
        else:
            content = request.form.get('content')

            local_user.bio = content
            print(f"{local_user.username} edited their user bio")
            return redirect(routes["user"].format(local_user.username))

@app.route(routes["signup"], methods=['GET', 'POST'])
def signup():
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)

    if local_user:

        print(f"{local_user.username} is already logged in")
        return redirect(routes["home"])
    else:
        if request.method == 'GET':

            return render_template("users/signup.html", routes=routes, user=local_user, error_message=None)
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            verify_password = request.form.get('verify_password')

            user_error = check_username(username)
            if user_error is not None:

                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message= user_error)

            password_error = check_password(password, verify_password)
            if password_error is not None:

                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message= password_error)

            try:
                test_user = User.read(connection, username)

                return render_template("users/signup.html", routes=routes, user=local_user,
                                       error_message=f'Username {test_user.username} already exists')
            except NameError:
                local_user = User.create(connection, username=username, password=password)
                token = Token(local_user.user_id)
                resp = make_response(redirect(routes["home"]))
                token.create(connection)

                resp.set_cookie('token', token.token_id)
                print(f'User {username} created')
                return resp




@app.route(routes["change_password"], methods=['GET', 'POST'])
def change_password():
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)


    if not local_user:

        return redirect(routes["home"])
    else:
        if request.method == 'GET':

            return render_template("settings/password.html", routes=routes, user=local_user, error_message=None)
        else:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            verify_new_password = request.form.get('verify_new_password')

            password_error = check_password(new_password, verify_new_password, old_password)
            if password_error is not None:
                return render_template("settings/password.html", routes=routes, user=local_user,
                                       error_message=password_error)

            if old_password == local_user.password_hash:
                local_user.password_hash = new_password
                print(f"{local_user.username} changed their password")
                return redirect(routes["user"].format(local_user.username))
            else:
                return render_template("settings/password.html", routes=routes, user=local_user,
                                       error_message=f'Incorrect old password')

@app.route(routes["about"])
def about():
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    return render_template('about.html', routes=routes, user=local_user)

@app.route(routes["logout"])
def logout():
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)

    if not local_user:

        return redirect(routes["home"])
    else:
        resp = redirect(routes["home"])
        token_id = request.cookies['token']
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tokens WHERE id = %s", (token_id,))
        connection.commit()
        cursor.close()
        resp.delete_cookie('token')

        return resp

@app.route(API["like_post"].format("<int:post_id>"), methods=['POST'])
def like_post(post_id):
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    try:
        json_data = request.get_json()
        try:
            if bool(json_data.get("like")):
                local_user.like(post_id)
            else:
                local_user.unlike(post_id)

            response = {
            "message": "Success"
            }
        except ValueError:
            response = {
                "message": "Cannot be done"
            }
        return jsonify(response)
    except NameError as e:
        abort(404, "Post not found")

@app.route(API["follow_user"].format("<username>"), methods=['POST'])
def follow_user(username):
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    try:
        json_data = request.get_json()
        followed_user = User.read(connection, username).user_id

        try:
            if bool(json_data.get("follow")):
                local_user.follow(followed_user)
            else:
                local_user.unfollow(followed_user)
            response = {
            "message": "Success"
            }
        except ValueError:
            response = {
                "message": "Cannot be done"
            }
        return jsonify(response)
    except NameError as e:
        abort(404, "User not found")

@app.route(API["comment_post"].format("<int:post_id>"), methods=['POST'])
def comment_post(post_id):
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    try:
        content = request.form.get("content")
        c = Comment.publish(connection, content, local_user.user_id, post_id)
        print(f'{local_user.username} commented on post {post_id}')
        return redirect(routes["post"].format(post_id))
    except NameError:
        abort(404, "Post not found")

@app.route(API["reply_comment"].format("<int:root_comment_id>"), methods=['POST'])
def reply_comment(root_comment_id):
    connection = get_db_connection()
    local_user = check_token(connection, request.cookies)
    try:
        content = request.form.get("content")
        root_comment = Comment.read(connection, root_comment_id)
        c = Comment.publish(connection, content, local_user.user_id, root_comment.comment_page, root_comment=root_comment_id)

        return redirect(routes["post"].format(root_comment.comment_page))
    except NameError:
        abort(404, "Post not found")

@app.route("/static/<path:file>")
def static_file(file):
    return static_file(file)

