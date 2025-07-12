from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from functools import wraps
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Utility Functions ---
def get_db_connection():
    conn = sqlite3.connect('news.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Login required to access admin panel.')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    top_posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC LIMIT 3').fetchall()
    breaking_news = conn.execute('SELECT title FROM posts ORDER BY created_at DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('index.html', posts=posts, top_posts=top_posts, breaking_news=breaking_news, year=datetime.now().year)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    return render_template('post.html', post=post)

@app.route('/category/<category>')
def category_page(category):
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts WHERE category = ? ORDER BY created_at DESC', (category,)).fetchall()
    conn.close()
    return render_template('index.html', posts=posts, top_posts=posts[:3], breaking_news=posts[:5], year=datetime.now().year)

@app.route('/videos')
def video_posts():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts WHERE video_url IS NOT NULL ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('index.html', posts=posts, top_posts=posts[:3], breaking_news=posts[:5], year=datetime.now().year)

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin.html', posts=posts, username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect('/admin')
        flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect('/')

@app.route('/post', methods=['POST'])
@login_required
def create_post():
    title = request.form['title']
    content = request.form['content']
    category = request.form['category']
    video_url = request.form.get('video_url', None)
    file = request.files['image']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO posts (title, content, image, category, video_url, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                 (title, content, filename, category, video_url, datetime.now()))
    conn.commit()
    conn.close()
    flash('News posted successfully!')
    return redirect('/admin')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    conn = get_db_connection()
    conn.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
    conn.commit()
    conn.close()
    flash('Subscribed successfully!')
    return redirect('/')

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Main ---
if __name__ == '__main__':
    if not os.path.exists('news.db'):
        conn = sqlite3.connect('news.db')
        conn.execute('''CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            category TEXT,
            video_url TEXT,
            created_at TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL
        )''')
        conn.execute('INSERT INTO admins (username, password) VALUES (?, ?)', ('admin', 'admin123'))
        conn.commit()
        conn.close()
    app.run(debug=True, port=5000)

 