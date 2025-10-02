

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"

# -------------------- UPLOADS --------------------
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------------- DATABASE --------------------
DATABASE = os.path.join(app.root_path, 'primeupdate.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            image TEXT,
            adsense_code TEXT
        )
    ''')
    # Subscribers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE
        )
    ''')
    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            name TEXT,
            comment TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    ''')
    db.commit()

# Initialize DB when app starts
with app.app_context():
    init_db()

# -------------------- ROUTES --------------------

# HOME PAGE
@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    # All posts
    cursor.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cursor.fetchall()
    # Breaking news (top 3)
    cursor.execute("SELECT * FROM posts WHERE category='Breaking' ORDER BY id DESC LIMIT 3")
    breaking_news = cursor.fetchall()
    # Trending
    cursor.execute("SELECT * FROM posts WHERE category='Trending' ORDER BY id DESC")
    trending_posts = cursor.fetchall()
    top_posts = breaking_news
    latest_posts = posts[:6]

    return render_template(
        "index.html",
        posts=posts,
        top_posts=top_posts,
        latest_posts=latest_posts,
        breaking_news=breaking_news,
        trending_posts=trending_posts,
        year=2025
    )

# VIEW SINGLE POST
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    db = get_db()
    cursor = db.cursor()
    # Fetch post
    cursor.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return "Post not found", 404

    # Add comment
    if request.method == 'POST':
        name = request.form['name']
        comment_text = request.form['comment']
        cursor.execute("INSERT INTO comments (post_id, name, comment) VALUES (?, ?, ?)",
                       (post_id, name, comment_text))
        db.commit()
        return redirect(url_for('view_post', post_id=post_id))

    # Fetch comments
    cursor.execute("SELECT * FROM comments WHERE post_id=? ORDER BY id DESC", (post_id,))
    comments = cursor.fetchall()

    # Breaking/trending for navbar
    cursor.execute("SELECT * FROM posts WHERE category='Breaking' ORDER BY id DESC LIMIT 3")
    breaking_news = cursor.fetchall()
    cursor.execute("SELECT * FROM posts WHERE category='Trending' ORDER BY id DESC")
    trending_posts = cursor.fetchall()

    return render_template(
        'post.html',
        post=post,
        comments=comments,
        breaking_news=breaking_news,
        trending=trending_posts,
        year=2025
    )

# SUBSCRIBE
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        db.commit()
        message = "Successfully subscribed!"
    except sqlite3.IntegrityError:
        message = "You are already subscribed."

    return redirect(url_for('index'))

# -------------------- ADMIN --------------------

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "password":
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid username or password"
            return render_template("login.html", error=error)
    return render_template("login.html")

# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# Admin dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']

        # Image
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        adsense_code = request.form.get("adsense_code", "")
        cursor.execute(
            "INSERT INTO posts (title, content, category, image, adsense_code) VALUES (?, ?, ?, ?, ?)",
            (title, content, category, filename, adsense_code)
        )
        db.commit()
        return redirect(url_for('admin_dashboard'))

    cursor.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cursor.fetchall()
    return render_template("admin.html", posts=posts)

# Edit post
@app.route('/admin/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return "Post not found", 404

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        adsense_code = request.form.get("adsense_code", "")

        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute("UPDATE posts SET image=? WHERE id=?", (filename, post_id))

        cursor.execute(
            "UPDATE posts SET title=?, content=?, category=?, adsense_code=? WHERE id=?",
            (title, content, category, adsense_code, post_id)
        )
        db.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_post.html', post=post)

# Delete post
@app.route('/admin/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM posts WHERE id=?", (post_id,))
    cursor.execute("DELETE FROM comments WHERE post_id=?", (post_id,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

# -------------------- CATEGORY --------------------
@app.route('/category/<category_name>')
def category_page(category_name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE category=? ORDER BY id DESC", (category_name,))
    posts = cursor.fetchall()
    cursor.execute("SELECT * FROM posts WHERE category='Breaking' ORDER BY id DESC LIMIT 3")
    breaking_news = cursor.fetchall()
    cursor.execute("SELECT * FROM posts WHERE category='Trending' ORDER BY id DESC")
    trending_posts = cursor.fetchall()
    top_posts = breaking_news
    latest_posts = posts[:6]
    return render_template(
        "index.html",
        posts=posts,
        top_posts=top_posts,
        latest_posts=latest_posts,
        breaking_news=breaking_news,
        trending_posts=trending_posts,
        year=2025
    )

# -------------------- UPLOADED FILES --------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- RUN --------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
