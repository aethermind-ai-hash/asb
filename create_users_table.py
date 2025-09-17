import sqlite3

# Connect to your database
DB_FILE = r"D:\ai-support-bot.db"
conn = sqlite3.connect(DB_FILE)

# Enable foreign key support
conn.execute("PRAGMA foreign_keys = ON;")

cursor = conn.cursor()

# Create/update the FAQs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    question TEXT NOT NULL,
    profile_pic TEXT,
    popular INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(user_email) REFERENCES users(email) ON DELETE CASCADE
);
""")

# Optional: create an index for faster queries on user_email
cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON faqs(user_email);")

conn.commit()
conn.close()

print("FAQs table created/updated successfully!")
