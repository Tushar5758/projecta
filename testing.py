from merged import LikePost, app, Post

with app.app_context():  # ✅ Create an application context
    for post in Post.query.all():
        print(f"Post ID: {post.id}, Type: {type(post.keywords)}, Value: {post.keywords}")
