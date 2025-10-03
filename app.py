import os
import sqlite3
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_from_directory, session, g, flash
)
from werkzeug.utils import secure_filename

# --- CONFIG ---
app = Flask(__name__)
app.secret_key = "supersecret_admin_key_change_this"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "primeupdate.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"  # change this in production

# --- DATABASE HELPERS ---
def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    c = db.cursor()
    # posts table (image filename, adsense_code)
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT,
        image TEXT,
        adsense_code TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # comments table
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
    )
    """)
    # subscribers table
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    db.commit()

# initialize DB on startup
with app.app_context():
    init_db()

# ------------- ROUTES ------------- #

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# HOME / index
@app.route('/')
def index():
    db = get_db()
    cur = db.cursor()

    # All posts (newest first)
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    # Breaking news = latest 3 posts (shown in breaking)
    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 3")
    breaking_news = cur.fetchall()

    # hero top_posts (use breaking_news)
    top_posts = breaking_news

    # Latest 10 posts
    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 10")
    latest_posts = cur.fetchall()

    # Trending = all posts (you can change logic later)
    trending_posts = posts

    year = datetime.utcnow().year

    return render_template(
        "index.html",
        posts=posts,
        breaking_news=breaking_news,
        top_posts=top_posts,
        latest_posts=latest_posts,
        trending_posts=trending_posts,
        year=year
    )

# VIEW single post + comment form
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = cur.fetchone()
    if not post:
        return "Post not found", 404

    if request.method == 'POST':
        name = request.form.get('name', 'Anonymous').strip()
        comment = request.form.get('comment', '').strip()
        if comment:
            cur.execute(
                "INSERT INTO comments (post_id, name, comment) VALUES (?, ?, ?)",
                (post_id, name, comment)
            )
            db.commit()
            return redirect(url_for('view_post', post_id=post_id))

    # fetch comments for this post
    cur.execute("SELECT * FROM comments WHERE post_id=? ORDER BY id DESC", (post_id,))
    comments = cur.fetchall()

    # also pass breaking & trending for header
    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 3")
    breaking_news = cur.fetchall()
    cur.execute("SELECT * FROM posts WHERE 1 ORDER BY id DESC")
    trending_posts = cur.fetchall()

    year = datetime.utcnow().year

    return render_template(
        "post.html",
        post=post,
        comments=comments,
        breaking_news=breaking_news,
        trending=trending_posts,
        year=year
    )

# SUBSCRIBE
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email', '').strip()
    if not email:
        flash("Please provide a valid email.", "warning")
        return redirect(url_for('index'))

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        db.commit()
        flash("Subscribed successfully — thank you!", "success")
    except sqlite3.IntegrityError:
        flash("You are already subscribed.", "info")
    return redirect(url_for('index'))

# ----------------- ADMIN ----------------- #

# Admin login (separate page)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "danger")
    # provide breaking/trending for base.html
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 3")
    breaking_news = cur.fetchall()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    trending = cur.fetchall()
    year = datetime.utcnow().year
    return render_template("login.html", breaking_news=breaking_news, trending=trending, year=year)

# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# Admin dashboard (view posts, add form)
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        # add post
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'General').strip()
        adsense_code = request.form.get('adsense_code', '').strip()

        # image upload
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur.execute(
            "INSERT INTO posts (title, content, category, image, adsense_code) VALUES (?, ?, ?, ?, ?)",
            (title, content, category, filename, adsense_code)
        )
        db.commit()
        flash("Post added.", "success")
        return redirect(url_for('admin_dashboard'))

    # GET: show posts
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    # Also show recent comments count per post (for quick overview)
    comment_counts = {}
    for p in posts:
        cur.execute("SELECT COUNT(*) as cnt FROM comments WHERE post_id=?", (p['id'],))
        r = cur.fetchone()
        comment_counts[p['id']] = r['cnt'] if r else 0

    year = datetime.utcnow().year
    return render_template("admin.html", posts=posts, comment_counts=comment_counts, year=year)

# Edit post
@app.route('/admin/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = cur.fetchone()
    if not post:
        return "Post not found", 404

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'General').strip()
        adsense_code = request.form.get('adsense_code', '').strip()

        # image upload (optional)
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("UPDATE posts SET image=? WHERE id=?", (filename, post_id))

        cur.execute(
            "UPDATE posts SET title=?, content=?, category=?, adsense_code=? WHERE id=?",
            (title, content, category, adsense_code, post_id)
        )
        db.commit()
        flash("Post updated.", "success")
        return redirect(url_for('admin_dashboard'))

    year = datetime.utcnow().year
    return render_template("edit_post.html", post=post, year=year)

# Delete post
@app.route('/admin/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM posts WHERE id=?", (post_id,))
    cur.execute("DELETE FROM comments WHERE post_id=?", (post_id,))
    db.commit()
    flash("Post deleted.", "info")
    return redirect(url_for('admin_dashboard'))

# Admin: view comments for a post
@app.route('/admin/comments/<int:post_id>')
def admin_comments(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = cur.fetchone()
    if not post:
        return "Post not found", 404

    cur.execute("SELECT * FROM comments WHERE post_id=? ORDER BY id DESC", (post_id,))
    comments = cur.fetchall()
    year = datetime.utcnow().year
    return render_template("admin_comments.html", post=post, comments=comments, year=year)

# Category page
@app.route('/category/<category_name>')
def category_page(category_name):
    db = get_db()
    cur = db.cursor()

    # Posts for this category
    cur.execute("SELECT * FROM posts WHERE category=? ORDER BY id DESC", (category_name,))
    posts = cur.fetchall()

    # Breaking news (top 3)
    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 3")
    breaking_news = cur.fetchall()

    # Trending (all posts)
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    trending = cur.fetchall()

    year = datetime.utcnow().year

    return render_template(
        "category.html",
        posts=posts,
        category_name=category_name,
        breaking_news=breaking_news,
        trending_posts=trending,  # make sure this matches your template variable
        year=year
    )


# ----------------- RUN ----------------- #
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
