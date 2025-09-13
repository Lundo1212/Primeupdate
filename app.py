import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change to something strong in production

# Database setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///news.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"
db = SQLAlchemy(app)


# Database model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255), nullable=True)


# Home Page
@app.route("/")
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    categories = [
        "Breaking",
        "Trending",
        "Politics",
        "Business",
        "Sports",
        "Entertainment",
        "Technology",
        "Health",
        "World",
        "Lifestyle",
        "Opinion",
    ]
    return render_template("index.html", posts=posts, categories=categories)


# Category Page
@app.route("/category/<string:category>")
def category_page(category):
    posts = Post.query.filter_by(category=category).order_by(Post.id.desc()).all()
    return render_template("category.html", posts=posts, category=category)


# Admin Login
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Replace with real credentials (e.g., env vars for security)
        if username == "admin" and password == "password":
            session["admin_logged_in"] = True
            return redirect("/admin")
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")


# Admin Dashboard (Add & View Posts)
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin_logged_in" not in session:
        return redirect("/admin/login")

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category = request.form["category"]

        image = request.files["image"]
        image_filename = None
        if image and image.filename != "":
            image_filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        new_post = Post(
            title=title, content=content, category=category, image=image_filename
        )
        db.session.add(new_post)
        db.session.commit()

        flash("Post added successfully!", "success")
        return redirect("/admin")

    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("admin.html", posts=posts)


# Admin Logout
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/")


# Uploaded Files Route
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
