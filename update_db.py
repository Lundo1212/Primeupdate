import sqlite3

# Connect to the database
conn = sqlite3.connect("primeupdate.db")
c = conn.cursor()

# Add 'category' column if it doesn't exist
try:
    c.execute("ALTER TABLE posts ADD COLUMN category TEXT")
    print("✅ Added 'category' column to posts table.")
except sqlite3.OperationalError:
    print("ℹ️ 'category' column already exists.")

# Add 'adsense_code' column if it doesn't exist
try:
    c.execute("ALTER TABLE posts ADD COLUMN adsense_code TEXT")
    print("✅ Added 'adsense_code' column to posts table.")
except sqlite3.OperationalError:
    print("ℹ️ 'adsense_code' column already exists.")

# Commit and close
conn.commit()
conn.close()
print("✅ Database update complete!")
