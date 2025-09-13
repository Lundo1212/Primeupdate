import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder for uploaded images
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory storage
posts = []
breaking_news = []
trending = []

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    top_posts = posts[:3]  # latest 3 posts for hero carousel
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
    return render_template(
        "post.html",
        post=post,
        breaking_news=breaking_news
    )

@app.route('/admin', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']

        # Image upload
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

        # Categorize
        if category.lower() == "breaking":
            breaking_news.insert(0, post)
        if category.lower() == "trending":
            trending.insert(0, post)

        return redirect(url_for('index'))

    return render_template("admin.html", breaking_news=breaking_news, trending=trending)

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
