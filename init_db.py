import sqlite3

DB_FILE = "ai-support-bot.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create FAQ table
cursor.execute("""
CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT UNIQUE NOT NULL,
    answer TEXT NOT NULL,
    popular BOOLEAN DEFAULT 0
)
""")

# Optional: insert a starter FAQ
cursor.execute("""
INSERT OR IGNORE INTO faq (question, answer, popular) VALUES
('What is AI Support Bot?', 'An intelligent assistant for your queries.', 1),
('How do I contact support?', 'You can email support@example.com', 1)
""")

conn.commit()
conn.close()

print("Database created successfully!")
