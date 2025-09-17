import sqlite3
import os

# Centralized DB file (matches main.py and analytics.py)
DB_FILE = os.getenv("DB_FILE", r"D:\ai-support-bot\ai-support-bot.db")


#===================
# New Client Added
#===================
def add_client(email, name=None, picture=None):
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO clients (email, name, profile_pic) VALUES (?, ?, ?)",
                (email.lower(), name or email.split("@")[0], picture or "/static/default_avatar.png")
            )
            conn.commit()
            client_id = get_client_id(email, conn)
            
            # Import here to avoid circular import
            from models_utils import create_client_model
            create_client_model(client_id)
        except sqlite3.IntegrityError:
            pass




def save_welcome_message_to_db(client_id, message):
    conn = sqlite3.connect("db.sqlite")  # make sure this matches your DB file
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clients SET welcome_message = ? WHERE id = ?",
        (message, client_id)
    )
    conn.commit()
    conn.close()

# ======================
# DATABASE CONNECTIONS
# ======================
def get_db():
    """
    Returns a SQLite connection with row_factory as Row and foreign key support enabled.
    Use with 'with get_db() as conn:' or manually close after use.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")  # optional but helps concurrency
    return conn



# ======================
# INITIALIZE TABLES
# ======================
def init_all_db():
    """
    Initialize all tables if they do not exist.
    """
    conn = get_db_connection()

    # Clients
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            company TEXT,
            role TEXT,
            subscription_plan TEXT DEFAULT 'free',
            status TEXT DEFAULT 'active',
            profile_pic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # FAQs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            popular BOOLEAN NOT NULL DEFAULT 0,
            UNIQUE(client_id, question),
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Welcome messages
    conn.execute("""
        CREATE TABLE IF NOT EXISTS welcome_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL UNIQUE,
            message TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Chat logs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Subscriptions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Bot settings
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            setting_name TEXT NOT NULL,
            setting_value TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Client integrations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS client_integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            integration_code TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Uploaded files
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Audit logs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            action TEXT NOT NULL,
            performed_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    # Analytics table (for logging events)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            user_id TEXT,
            event_type TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Client models table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS client_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL UNIQUE,
            model_path TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()
    print("✅ All tables initialized successfully.")


# Initialize tables on import
init_all_db()


# ======================
# HELPER FUNCTIONS
# ======================

def read_faq(client_id=None, conn=None):
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    if client_id:
        rows = conn.execute("SELECT question, answer, popular FROM faqs WHERE client_id=?", (client_id,)).fetchall()
    else:
        rows = conn.execute("SELECT question, answer, popular FROM faqs").fetchall()
    if close_conn:
        conn.close()
    return {r["question"]: {"answer": r["answer"], "popular": bool(r["popular"])} for r in rows}


def is_client(email):
    with get_db() as conn:
        row = conn.execute("SELECT 1 FROM clients WHERE LOWER(email)=LOWER(?)", (email.lower(),)).fetchone()
        return bool(row)


def get_client_id(email, conn=None):
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    row = conn.execute("SELECT id FROM clients WHERE LOWER(email)=LOWER(?)", (email.lower(),)).fetchone()
    if close_conn:
        conn.close()
    return row["id"] if row else None


def add_or_update_user_integration(email, code, conn=None):
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    client_id = get_client_id(email, conn)
    if not client_id:
        if close_conn:
            conn.close()
        return
    existing = conn.execute("SELECT id FROM client_integrations WHERE client_id=?", (client_id,)).fetchone()
    if existing:
        conn.execute("UPDATE client_integrations SET integration_code=? WHERE client_id=?", (code, client_id))
        action = "Updated integration code"
    else:
        conn.execute("INSERT INTO client_integrations (client_id, integration_code) VALUES (?, ?)", (client_id, code))
        action = "Added integration code"
    conn.execute("INSERT INTO audit_logs (client_id, action, performed_by) VALUES (?, ?, ?)", (client_id, action, email))
    conn.commit()
    if close_conn:
        conn.close()


def delete_faq_in_db(client_id, question):
    with get_db() as conn:
        conn.execute("DELETE FROM faqs WHERE client_id=? AND question=?", (client_id, question))
        conn.execute("INSERT INTO audit_logs (client_id, action, performed_by) VALUES (?, ?, ?)",
                     (client_id, f"Deleted FAQ: {question}", None))
        conn.commit()


def log_audit(client_id, action, performed_by=None):
    with get_db() as conn:
        conn.execute("INSERT INTO audit_logs (client_id, action, performed_by) VALUES (?, ?, ?)",
                     (client_id, action, performed_by))
        conn.commit()


# ======================
# SUBSCRIPTION / PLAN HELPERS
# ======================

def get_user_plan(client_id: int) -> str:
    """Return the subscription plan of the client"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT subscription_plan FROM clients WHERE id=?", (client_id,))
        row = cur.fetchone()
        return row["subscription_plan"] if row else "demo"
    finally:
        conn.close()


def get_faq_count(client_id: int) -> int:
    """
    Returns the maximum allowed FAQs for a given client based on their subscription plan.
    """
    plan = get_user_plan(client_id).lower()
    limits = {
        "demo": 5,
        "onetime": 20,
        "basic": 50,
        "standard": 100,
        "premium": 200
    }
    return limits.get(plan, 5)


def get_ai_request_count(client_id: int) -> int:
    """Return how many AI requests the client has used this month"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as used
            FROM analytics
            WHERE client_id=? AND event_type='ai_request'
            AND strftime('%Y-%m', timestamp) = strftime('%Y-%m','now')
        """, (client_id,))
        row = cur.fetchone()
        return row["used"] or 0
    finally:
        conn.close()
