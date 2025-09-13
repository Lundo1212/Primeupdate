import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session

# Upload folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Temporary in-memory storage
posts = []
breaking_news = []
trending = []

# Admin credentials
ADMIN_USER = "admin"
ADMIN_PASS = "password"

# -------------------- ROUTES --------------------

# Home page
@app.route('/')
def index():
    top_posts = posts[:3]  # Hero carousel
    trending_posts = [p for p in posts if p['category'].lower() == 'trending']
    return render_template('index.html', posts=posts, top_posts=top_posts,
                           trending_posts=trending_posts,
                           breaking_news=breaking_news)

# View post
@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    return render_template('post.html', post=post, breaking_news=breaking_news, trending=trending)

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html', breaking_news=breaking_news, trending=trending)

# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# Admin dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']

        # Handle image
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Create post
        post = {
            'id': len(posts) + 1,
            'title': title,
            'content': content,
            'category': category,
            'image': filename
        }
        posts.append(post)

        # Update breaking/trending
        if category.lower() == 'breaking':
            breaking_news.insert(0, post)
        if category.lower() == 'trending':
            trending.insert(0, post)

        return redirect(url_for('admin_dashboard'))

    return render_template('admin.html', posts=posts, breaking_news=breaking_news, trending=trending)

# Delete post
@app.route('/admin/delete/<int:post_id>')
def delete_post(post_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    global posts, breaking_news, trending
    posts = [p for p in posts if p['id'] != post_id]
    breaking_news = [p for p in breaking_news if p['id'] != post_id]
    trending = [p for p in trending if p['id'] != post_id]
    return redirect(url_for('admin_dashboard'))

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- MAIN --------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

