import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Folder for uploaded images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory storage
posts = []
breaking_news = []
trending = []

# Admin credentials (simple)
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    top_posts = posts[:3]
    trending_posts = [p for p in posts if p['category'].lower() == "trending"]
    return render_template(
        "index.html",
        posts=posts,
        top_posts=top_posts,
        trending_posts=trending_posts,
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

@app.route('/category/<string:category_name>')
def category_page(category_name):
    filtered_posts = [p for p in posts if p['category'].lower() == category_name.lower()]
    top_posts = filtered_posts[:3]
    trending_posts = [p for p in filtered_posts if p['category'].lower() == 'trending']
    return render_template(
        'index.html',
        posts=filtered_posts,
        top_posts=top_posts,
        trending_posts=trending_posts,
        breaking_news=breaking_news,
        trending=trending,
        category_filter=category_name
    )

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']

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
            'image': filename
        }

        posts.append(post)

        if category.lower() == "breaking":
            breaking_news.insert(0, post)
        if category.lower() == "trending":
            trending.insert(0, post)

        return redirect(url_for('admin_dashboard'))

    return render_template("admin.html", posts=posts)

@app.route('/admin/delete/<int:post_id>')
def delete_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    global posts, breaking_news, trending
    posts = [p for p in posts if p['id'] != post_id]
    breaking_news = [p for p in breaking_news if p['id'] != post_id]
    trending = [p for p in trending if p['id'] != post_id]
    return redirect(url_for('admin_dashboard'))

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- MAIN --------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
