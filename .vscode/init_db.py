# init_db.py
import sqlite3

conn = sqlite3.connect('news.db')
c = conn.cursor()

# Create posts table
c.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image TEXT,
        category TEXT,
        video_url TEXT,
        created_at TEXT NOT NULL
    )
''')

# Create admins table
c.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

# Create subscribers table
c.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL
    )
''')

# Insert default admin user if not exists
c.execute("SELECT COUNT(*) FROM admins WHERE username='admin'")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', 'admin123'))

conn.commit()
conn.close()
print("Database initialized successfully.")
