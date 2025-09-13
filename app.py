import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # replace with a strong key

# Folder for uploaded images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory storage (replace with DB later)
posts = []
breaking_news = []
trending = []
adsense_code = ""  # Google AdSense code

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    top_posts = posts[:3]  # first 3 posts for carousel
    trending_posts = [p for p in posts if p['category'].lower() == 'trending']
    return render_template(
        'index.html',
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

# Admin login
@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Replace with your admin credentials
        if username == 'admin' and password == 'password123':
            session['admin_logged_in'] = True
            return redirect(url_for('add_post'))
        else:
            return render_template(
                'login.html',
                error='Invalid credentials',
                breaking_news=breaking_news,
                trending=trending
            )

    return render_template(
        'login.html',
        breaking_news=breaking_news,
        trending=trending
    )

# Admin dashboard
@app.route('/admin', methods=['GET', 'POST'])
def add_post():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    global adsense_code

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

        # Update breaking and trending lists
        if category.lower() == 'breaking':
            breaking_news.insert(0, post)
        if category.lower() == 'trending':
            trending.insert(0, post)

        return redirect(url_for('add_post'))

    return render_template(
        'admin.html',
        posts=posts,
        breaking_news=breaking_news,
        trending=trending,
        adsense_code=adsense_code
    )

# Edit post
@app.route('/admin/edit/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404

    post['title'] = request.form['title']
    post['category'] = request.form['category']
    post['content'] = request.form['content']

    image_file = request.files.get('image')
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        post['image'] = filename

    # Update breaking/trending lists
    global breaking_news, trending
    breaking_news = [p for p in posts if p['category'].lower() == 'breaking']
    trending = [p for p in posts if p['category'].lower() == 'trending']

    return redirect(url_for('add_post'))

# Delete post
@app.route('/admin/delete/<int:post_id>')
def delete_post(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    global posts, breaking_news, trending
    posts = [p for p in posts if p['id'] != post_id]
    breaking_news = [p for p in posts if p['category'].lower() == 'breaking']
    trending = [p for p in posts if p['category'].lower() == 'trending']

    return redirect(url_for('add_post'))

# Update AdSense code
@app.route('/admin/update_adsense', methods=['POST'])
def update_adsense():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    global adsense_code
    adsense_code = request.form.get('adsense_code', '')
    return redirect(url_for('add_post'))

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Logout
@app.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# -------------------- MAIN --------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
