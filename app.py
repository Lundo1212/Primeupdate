import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session management

# Folder for uploaded images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Temporary in-memory storage
posts = []
breaking_news = []
trending = []

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"


# -------------------- ROUTES --------------------

@app.route('/')
def index():
    top_posts = breaking_news[:3]  # Hero carousel
    return render_template(
        "index.html",
        top_posts=top_posts,
        trending_posts=trending,
        posts=posts
    )


@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    return render_template(
        'post.html',
        post=post
    )


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template(
                "login.html",
                error="Invalid credentials"
            )

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
        post_id = request.form.get('post_id')
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

        if post_id:  # Editing existing post
            post = next((p for p in posts if p['id'] == int(post_id)), None)
            if post:
                post['title'] = title
                post['content'] = content
                post['category'] = category
                if filename:
                    post['image'] = filename
        else:  # New post
            post = {
                'id': len(posts) + 1,
                'title': title,
                'content': content,
                'category': category,
                'image': filename,
                'adsense_code': request.form.get("adsense_code", "")
            }
            posts.insert(0, post)  # latest first
            breaking_news.insert(0, post)  # Automatically breaking
            if category.lower() == "trending":
                trending.insert(0, post)

        return redirect(url_for('admin_dashboard'))

    return render_template(
        "admin.html",
        posts=posts,
        breaking_news=breaking_news,
        trending=trending
    )


@app.route('/admin/edit/<int:post_id>', methods=['GET'])
def edit_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    return render_template("admin.html", post_to_edit=post, posts=posts)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/category/<category_name>')
def category_page(category_name):
    filtered_posts = [p for p in posts if p['category'].lower() == category_name.lower()]
    return render_template(
        "index.html",
        top_posts=breaking_news[:3],
        trending_posts=trending,
        posts=filtered_posts
    )


# -------------------- MAIN --------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
