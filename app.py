from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from email.message import EmailMessage
import smtplib
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Multiple admin accounts
ADMINS = [
    {"username": "admin1", "password": "password1"},
    {"username": "editor2", "password": "password2"}
]

# ✅ Email setup
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_email_password"  # Use App Password for Gmail!

# ✅ Init database
def init_db():
    conn = sqlite3.connect('primeupdate.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        image_path TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        comment TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

# ✅ Home page - show all posts
@app.route('/')
def index():
    conn = sqlite3.connect('primeupdate.db')
    c = conn.cursor()
    c.execute('SELECT id, title, content, image_path, timestamp FROM posts ORDER BY timestamp DESC')
    posts = c.fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

# ✅ View single post
@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = sqlite3.connect('primeupdate.db')
    c = conn.cursor()
    c.execute('SELECT id, title, content, image_path, timestamp FROM posts WHERE id=?', (post_id,))
    post = c.fetchone()
    c.execute('SELECT comment, timestamp FROM comments WHERE post_id=? ORDER BY timestamp DESC', (post_id,))
    comments = c.fetchall()
    conn.close()
    return render_template('post.html', post=post, comments=comments)

# ✅ Add comment
@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    comment = request.form.get('comment')
    conn = sqlite3.connect('primeupdate.db')
    c = conn.cursor()
    c.execute('INSERT INTO comments (post_id, comment) VALUES (?,?)', (post_id, comment))
    conn.commit()
    conn.close()
    return redirect(url_for('view_post', post_id=post_id))

# ✅ Subscribe
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    conn = sqlite3.connect('primeupdate.db')
    c = conn.cursor()
    c.execute('INSERT INTO subscriptions (email) VALUES (?)', (email,))
    conn.commit()
    conn.close()
    flash('You have subscribed successfully!')
    return redirect(url_for('index'))

# ✅ Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for admin in ADMINS:
            if admin['username'] == username and admin['password'] == password:
                session['admin_user'] = username
                return redirect(url_for('admin'))
        flash('Invalid credentials')
    return render_template('login.html')

# ✅ Admin dashboard to post
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin_user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files['image']
        image_path = None
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            image_path = file_path
        conn = sqlite3.connect('primeupdate.db')
        c = conn.cursor()
        c.execute('INSERT INTO posts (title, content, image_path) VALUES (?,?,?)',
                  (title, content, image_path))
        conn.commit()
        new_post_id = c.lastrowid

        # 🔥 Fetch all emails and send them new post notification
        c.execute('SELECT email FROM subscriptions')
        emails = c.fetchall()
        for e in emails:
            msg = EmailMessage()
            msg['Subject'] = f"New article on PrimeUpdate: {title}"
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = e[0]
            msg.set_content(f"Check out our new article!\n\n{title}\nRead more at: http://127.0.0.1:5000/post/{new_post_id}")
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

        conn.close()
        flash('Post created and notifications sent!')
        return redirect(url_for('index'))
    return render_template('admin.html')

# ✅ Logout
@app.route('/logout')
def logout():
    session.pop('admin_user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

