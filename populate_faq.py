import sqlite3

DB_FILE = "ai-support-bot.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Sample FAQ data
faq_data = [
    ("What is AI Support Bot?", "An intelligent assistant that answers your questions instantly.", 1),
    ("How do I contact support?", "You can email us at support@example.com.", 1),
    ("How can I update my profile?", "Go to the settings page in your account to update your profile.", 0),
    ("Can I add new questions?", "Yes, use the admin panel to add or edit FAQs.", 0),
    ("Is my data safe?", "Yes, your data is stored securely in our database.", 1),
    ("Which languages are supported?", "Currently, the bot supports English only.", 0),
    ("How do I reset my password?", "Use the 'Forgot Password' option on the login page.", 0),
]

# Insert data into faq table
for question, answer, popular in faq_data:
    cursor.execute("""
        INSERT OR IGNORE INTO faq (question, answer, popular)
        VALUES (?, ?, ?)
    """, (question, answer, popular))

conn.commit()
conn.close()
print("Sample FAQs added successfully!")
