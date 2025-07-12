import sqlite3

# Initialize database and ensure required tables exist
def initialize_db():
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

    # Insert default admin if not exists
    c.execute('SELECT * FROM admins WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO admins (username, password) VALUES (?, ?)', ('admin', 'admin123'))

    # Create subscribers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_db()
    print("✅ Database initialized successfully!")
