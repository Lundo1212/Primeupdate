import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

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
    """Homepage showing all posts + breaking + trending"""
    return render_template(
        "index.html",
        posts=posts,
        breaking_news=breaking_news,
        trending=trending
    )


@app.route('/post/<int:post_id>')
def view_post(post_id):
    """View single post"""
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    return render_template(
        "post.html",
        post=post,
        breaking_news=breaking_news,
        trending=trending
    )


@app.route('/admin', methods=['GET', 'POST'])
def add_post():
    """Admin dashboard to add new posts"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')

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

        posts.append(post)

        # Add to breaking news if category matches
        if category and category.lower() == "breaking":
            breaking_news.insert(0, post)

        # Add to trending if category matches
        if category and category.lower() == "trending":
            trending.insert(0, post)

        return redirect(url_for('index'))

    return render_template(
        "admin.html",
        posts=posts,  # Show all posts in admin page
        breaking_news=breaking_news,
        trending=trending
    )


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# -------------------- MAIN --------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
