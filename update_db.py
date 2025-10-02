import sqlite3

# Connect to the database
conn = sqlite3.connect("primeupdate.db")
c = conn.cursor()

# Function to safely add a column if it doesn't exist
def add_column_if_not_exists(table, column_def):
    column_name = column_def.split()[0]
    c.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in c.fetchall()]
    if column_name not in columns:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        print(f"✅ Added column '{column_name}' to {table}.")
    else:
        print(f"ℹ️ Column '{column_name}' already exists in {table}.")

# Add missing columns to posts table
add_column_if_not_exists("posts", "category TEXT")
add_column_if_not_exists("posts", "image TEXT")
add_column_if_not_exists("posts", "adsense_code TEXT")

conn.commit()
conn.close()
print("✅ Database updated successfully!")

