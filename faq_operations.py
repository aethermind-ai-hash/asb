import sqlite3

DB_FILE = "ai_support_bot.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

# Add a new FAQ
def add_faq(question, answer, popular=False):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO faqs (question, answer, popular) VALUES (?, ?, ?)",
                   (question, answer, int(popular)))
    conn.commit()
    conn.close()

# Fetch all FAQs
def get_all_faqs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, answer, popular FROM faqs ORDER BY popular DESC, question ASC")
    faqs = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "question": f[1], "answer": f[2], "popular": bool(f[3])} for f in faqs]

# Update an FAQ
def update_faq(faq_id, question, answer, popular):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE faqs SET question=?, answer=?, popular=? WHERE id=?",
                   (question, answer, int(popular), faq_id))
    conn.commit()
    conn.close()

# Delete an FAQ
def delete_faq(faq_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faqs WHERE id=?", (faq_id,))
    conn.commit()
    conn.close()
