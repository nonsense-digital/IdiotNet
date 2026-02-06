from flask import Blueprint, render_template, abort, request, redirect, make_response, jsonify
from helpers.auth import *
from helpers.db import *
from models.client import Client
from models.comment import Comment
from models.permissions import PunishmentType
from models.user import User, check_username, check_password
from routes import routes, API

api = Blueprint('api', __name__, template_folder='../templates')

# api endpoint to like/unlike a post
# returns an error message if the request failed, and a success message if it succeeded
@api.route(API["like_post"].format("<int:post_id>"), methods=['POST'])
def like_post(post_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    try:
        json_data = request.get_json()
        try:
            if bool(json_data.get("like")):
                local_user.like(post_id)
                action = "liked"
            else:
                local_user.unlike(post_id)
                action = "unliked"

            response = {
            "message": "Success"
            }
            current_app.logger.info(
                f"[IP {request.remote_addr}] {local_user.username} {action} post {post_id}")
        except ValueError:
            response = {
                "message": "Cannot be done"
            }
            current_app.logger.error(
                f"[IP {request.remote_addr}] {local_user.username} failed to {post_id}")
        return jsonify(response)
    except NameError as e:
        abort(404, "Post not found")

# api endpoint to follow/unfollow a user
# returns an error message if the request failed, and a success message if it succeeded
@api.route(API["follow_user"].format("<username>"), methods=['POST'])
def follow_user(username):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    try:
        json_data = request.get_json()
        followed_user = User.read(connection, username).user_id

        try:
            if bool(json_data.get("follow")):
                local_user.follow(followed_user)
                action = "followed"
            else:
                local_user.unfollow(followed_user)
                action = "unfollowed"
            response = {
            "message": "Success"
            }
            current_app.logger.info(
                f"[IP {request.remote_addr}] {local_user.username} {action} user {username}")
        except ValueError:
            response = {
                "message": "Cannot be done"
            }
            current_app.logger.error(
                f"[IP {request.remote_addr}] {local_user.username} failed to follow/unfollow user {username}")
        return jsonify(response)
    except NameError as e:
        abort(404, "User not found")

# api endpoint to comment on a post
@api.route(API["comment_post"].format("<int:post_id>"), methods=['POST'])
def comment_post(post_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    try:
        if local_user.punishment_status != PunishmentType.MUTE:
            content = request.form.get("content")
            comment = Comment.publish(connection, content, local_user.user_id, post_id)
            current_app.logger.info(
                f"[IP {request.remote_addr}] {local_user.username} created comment {comment.comment_id} on post {post_id}")
        return redirect(routes["post"].format(post_id))
    except NameError:
        current_app.logger.warning(f"[IP {request.remote_addr}] {local_user.username} cannot comment,  Post {post_id} not found.")
        abort(404, "Post not found")

# api endpoint to reply to a comment
@api.route(API["reply_comment"].format("<int:root_comment_id>"), methods=['POST'])
def reply_comment(root_comment_id):
    connection = get_db_connection()
    local_user = get_authenticated_user(connection, request.cookies)
    client = Client(connection, request.remote_addr)
    try:
        content = request.form.get("content")
        root_comment = Comment.read(connection, root_comment_id)
        if local_user.punishment_status != PunishmentType.MUTE and client.punishment_status != PunishmentType.MUTE:
            comment = Comment.publish(connection, content, local_user.user_id, root_comment.comment_page, root_comment=root_comment_id)
            current_app.logger.info(
                f"[IP {request.remote_addr}] {local_user.username} created comment {comment.comment_id} as a reply to {root_comment_id}")
        return redirect(routes["post"].format(root_comment.comment_page))
    except NameError:
        current_app.logger.warning(
            f"[IP {request.remote_addr}] {local_user.username} cannot reply, Comment {root_comment_id} not found.")
        abort(404, "Root comment not found")