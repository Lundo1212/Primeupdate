import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Folder for uploaded images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Temporary in-memory storage (replace with DB later)
posts = []
breaking_news = []
trending = []

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    return render_template(
        "index.html",
        posts=posts,
        breaking_news=breaking_news,
        trending=trending
    )

@app.route('/category/<category>')
def category_page(category):
    filtered_posts = [p for p in posts if p['category'].lower() == category.lower()]
    return render_template(
        'index.html',
        posts=filtered_posts,
        breaking_news=breaking_news,
        trending=trending
    )

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    return render_template(
        'post.html',
        post=post,
        breaking_news=breaking_news,
        trending=trending
    )

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Simple credentials (replace with DB in production)
        if username == "admin" and password == "password":
            session['admin_logged_in'] = True
            return redirect(url_for('add_post'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def add_post():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        adsense_code = request.form.get('adsense_code')  # Optional AdSense

        # Handle image upload
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        post = {
            'id': len(posts) + 1,
            'title': title,
            'content': content,
            'category': category,
            'image': filename,
            'adsense': adsense_code
        }

        posts.append(post)

        if category.lower() == "breaking":
            breaking_news.insert(0, post)
        if category.lower() == "trending":
            trending.insert(0, post)

        return redirect(url_for('add_post'))

    return render_template(
        "admin.html",
        posts=posts,
        breaking_news=breaking_news,
        trending=trending
    )

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- MAIN --------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
