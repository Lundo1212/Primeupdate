import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

posts = []
trending = []
breaking_news = []
adsense_code = ""

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# -------------------- PUBLIC --------------------
@app.route('/')
def index():
    top_posts = posts[:3]
    trending_posts = trending[:3]
    other_posts = [p for p in posts if p not in trending_posts]
    return render_template(
        "index.html",
        posts=other_posts,
        top_posts=top_posts,
        trending_posts=trending_posts,
        breaking_news=breaking_news
    )

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    return render_template("post.html", post=post, breaking_news=breaking_news)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- ADMIN --------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('add_post'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

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
            'image': filename
        }

        posts.append(post)

        if category.lower() == "trending":
            trending.insert(0, post)
        if category.lower() == "breaking":
            breaking_news.insert(0, post)

        return redirect(url_for('add_post'))

    return render_template(
        "admin.html",
        posts=posts,
        trending=trending,
        breaking_news=breaking_news,
        adsense_code=adsense_code
    )

# -------------------- EDIT / DELETE --------------------
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

        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post['image'] = filename

        if post in trending: trending.remove(post)
        if post in breaking_news: breaking_news.remove(post)
        if post['category'].lower() == "trending": trending.insert(0, post)
        if post['category'].lower() == "breaking": breaking_news.insert(0, post)

        return redirect(url_for('add_post'))

    return render_template('edit_post.html', post=post)

@app.route('/admin/delete/<int:post_id>')
def delete_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    global posts, trending, breaking_news
    post = next((p for p in posts if p['id'] == post_id), None)
    if post:
        posts.remove(post)
        if post in trending: trending.remove(post)
        if post in breaking_news: breaking_news.remove(post)
    return redirect(url_for('add_post'))

# -------------------- ADSENSE --------------------
@app.route('/admin/update_adsense', methods=['POST'])
def update_adsense():
    global adsense_code
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    adsense_code = request.form['adsense_code']
    return redirect(url_for('add_post'))

# -------------------- MAIN --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
