import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

# Folder for uploaded images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Temporary in-memory storage (replace with DB later)
posts = []
breaking_news = []
trending_posts = []

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    # Top 3 breaking news for Hero Slideshow
    top_posts = breaking_news[:3]
    return render_template(
        "index.html",
        top_posts=top_posts,
        trending_posts=trending_posts,
        posts=posts,
        breaking_news=breaking_news  # ensure templates can access this
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
        trending_posts=trending_posts
    )

@app.route('/admin', methods=['GET', 'POST'])
def add_post():
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

        # Create post object
        post = {
            'id': len(posts) + 1,
            'title': title,
            'content': content,
            'category': category,
            'image': filename
        }

        # Add post to main list (latest posts on top)
        posts.insert(0, post)

        # Add post to breaking news immediately
        breaking_news.insert(0, post)

        # If category is Trending, add to trending
        if category.lower() == "trending":
            trending_posts.insert(0, post)

        return redirect(url_for('add_post'))

    return render_template(
        "admin.html",
        posts=posts,
        breaking_news=breaking_news,
        trending_posts=trending_posts
    )

# -------------------- EDIT POST --------------------
@app.route('/admin/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404

    if request.method == 'POST':
        post['title'] = request.form['title']
        post['content'] = request.form['content']
        post['category'] = request.form['category']

        # Handle new image if uploaded
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            post['image'] = filename

        # Update breaking/trending lists
        if post not in breaking_news:
            breaking_news.insert(0, post)
        if post['category'].lower() == "trending" and post not in trending_posts:
            trending_posts.insert(0, post)

        return redirect(url_for('add_post'))

    return render_template(
        "edit_post.html",
        post=post,
        posts=posts,
        breaking_news=breaking_news,
        trending_posts=trending_posts
    )

# -------------------- DELETE POST --------------------
@app.route('/admin/delete/<int:post_id>')
def delete_post(post_id):
    global posts, breaking_news, trending_posts
    post = next((p for p in posts if p['id'] == post_id), None)
    if post:
        posts = [p for p in posts if p['id'] != post_id]
        breaking_news = [p for p in breaking_news if p['id'] != post_id]
        trending_posts = [p for p in trending_posts if p['id'] != post_id]
    return redirect(url_for('add_post'))

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- MAIN --------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
