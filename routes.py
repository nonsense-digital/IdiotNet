routes = {
    "home": "/",
    "about": "/about",
    "post": "/posts/{}",
    "latest": "/posts/latest",
    "new_post": "/posts/new",
    "post_edit": "/posts/{}/edit",
    "login": "/users/login",
    "signup": "/users/signup",
    "user": "/users/{}",
    "logout": "/users/logout",
    "user_posts": "/users/{}/posts",
    "user_edit": "/users/{}/edit",
    "user_liked_posts": "/users/{}/liked-posts",
    "user_following": "/users/{}/following",
    "user_followers": "/users/{}/followers",
    "change_password": "/settings/password"
}

API = {
    "like_post": "/api/posts/{}/like",
    "follow_user": "/api/users/{}/follow",
    "comment_post": "/api/posts/{}/comment",
    "reply_comment": "/api/comments/{}/reply",
}