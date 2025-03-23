from merged import LikePost, app

with app.app_context():  # ✅ Create an application context
    likes = LikePost.query.all()
    print("Likes in Database:", likes)  # ✅ Print the likes to see if they exist

