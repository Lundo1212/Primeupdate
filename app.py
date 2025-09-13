import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For sessions

# Upload folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Temporary storage
posts = []
breaking_news = []
trending_posts = []

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    top_posts = breaking_news[:3]
    return render_template(
        "index.html",
        top_posts=top_posts,
        trending_posts=trending_posts,
        posts=posts
    )

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    return render_template('post.html', post=post)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- ADMIN --------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
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
        # Add new post
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']

        # Image upload
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        post = {
            'id': len(posts) + 1,
            'title': title,
            'content': content,
            'category': category,
            'image': filename,
            'adsense_code': request.form.get("adsense_code", "")
        }

        posts.insert(0, post)
        breaking_news.insert(0, post)
        if category.lower() == "trending":
            trending_posts.insert(0, post)

        return redirect(url_for('admin_dashboard'))

    return render_template("admin.html", posts=posts)

@app.route('/admin/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404

    if request.method == 'POST':
        post['title'] = request.form['title']
        post['content'] = request.form['content']
        post['category'] = request.form['category']
        post['adsense_code'] = request.form.get("adsense_code", "")
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post['image'] = filename
        # Update breaking news/trending lists
        if post not in breaking_news:
            breaking_news.insert(0, post)
        if post['category'].lower() == 'trending' and post not in trending_posts:
            trending_posts.insert(0, post)
        return redirect(url_for('admin_dashboard'))

    return render_template("edit_post.html", post=post)

@app.route('/admin/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    global posts, breaking_news, trending_posts
    posts = [p for p in posts if p['id'] != post_id]
    breaking_news = [p for p in breaking_news if p['id'] != post_id]
    trending_posts = [p for p in trending_posts if p['id'] != post_id]
    return redirect(url_for('admin_dashboard'))

# -------------------- CATEGORY --------------------
@app.route('/category/<category_name>')
def category_page(category_name):
    filtered_posts = [p for p in posts if p['category'].lower() == category_name.lower()]
    top_posts = breaking_news[:3]
    return render_template(
        "index.html",
        top_posts=top_posts,
        trending_posts=trending_posts,
        posts=filtered_posts
    )

# -------------------- MAIN --------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
