from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Sample data (replace with DB later)
posts = [
    {
        "id": 1,
        "title": "Government Unveils New Policy",
        "content": "The government has unveiled a new policy...",
        "views": 1200,
        "category": "Politics",
        "image": "https://via.placeholder.com/800x400.png?text=Policy+News",
        "date": datetime.now()
    },
    {
        "id": 2,
        "title": "Sports Championship Kicks Off",
        "content": "The annual sports championship has started...",
        "views": 980,
        "category": "Sports",
        "image": "https://via.placeholder.com/800x400.png?text=Sports+News",
        "date": datetime.now()
    },
    {
        "id": 3,
        "title": "Tech Giants Announce Merger",
        "content": "Two leading tech companies have announced a merger...",
        "views": 1500,
        "category": "Technology",
        "image": "https://via.placeholder.com/800x400.png?text=Tech+News",
        "date": datetime.now()
    }
]

@app.route('/')
def index():
    breaking_news = posts[:5]  # first 5 for breaking news
    trending = sorted(posts, key=lambda x: x['views'], reverse=True)[:3]  # top 3 most viewed
    return render_template("index.html", posts=posts, breaking_news=breaking_news, trending=trending)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return "Post not found", 404
    breaking_news = posts[:5]
    trending = sorted(posts, key=lambda x: x['views'], reverse=True)[:3]
    return render_template("post.html", post=post, breaking_news=breaking_news, trending=trending)

@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        new_post = {
            "id": len(posts) + 1,
            "title": request.form["title"],
            "content": request.form["content"],
            "views": 0,
            "category": request.form["category"],
            "image": request.form["image"],
            "date": datetime.now()
        }
        posts.append(new_post)
        return redirect(url_for("index"))
    breaking_news = posts[:5]
    trending = sorted(posts, key=lambda x: x['views'], reverse=True)[:3]
    return render_template("add_post.html", breaking_news=breaking_news, trending=trending)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT env variable
    app.run(host="0.0.0.0", port=port, debug=True)
from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/uploads'), filename)





 