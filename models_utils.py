import os
import shutil
from deeppavlov import build_model

BASE_MODEL_DIR = os.path.join(os.getcwd(), "models")
TEMPLATE_MODEL_DIR = os.path.join(BASE_MODEL_DIR, "faq_template")  # Pre-trained template


def create_client_model(client_id):
    """
    Creates a folder for the client's FAQ model by copying the template.
    Saves the path in client_models table.
    """
    from db import get_db_connection  # moved import here to avoid circular import

    os.makedirs(BASE_MODEL_DIR, exist_ok=True)

    client_model_path = os.path.join(BASE_MODEL_DIR, f"client_{client_id}", "faq_model")
    os.makedirs(client_model_path, exist_ok=True)

    if os.path.exists(TEMPLATE_MODEL_DIR):
        shutil.copytree(TEMPLATE_MODEL_DIR, client_model_path, dirs_exist_ok=True)

    # Save path in DB
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO client_models (client_id, model_path)
            VALUES (?, ?)
            ON CONFLICT(client_id) DO UPDATE SET model_path=excluded.model_path
        """, (client_id, client_model_path))
        conn.commit()
    finally:
        conn.close()

    return client_model_path


def load_client_model(client_id):
    """
    Loads a client-specific DeepPavlov model.
    If no model exists yet, creates one automatically.
    """
    from db import get_db_connection  # moved import here to avoid circular import

    conn = get_db_connection()
    row = conn.execute("SELECT model_path FROM client_models WHERE client_id=?", (client_id,)).fetchone()
    conn.close()

    if not row:
        # Auto-create model if missing
        model_path = create_client_model(client_id)
    else:
        model_path = row["model_path"]

    config_file = os.path.join(model_path, "config.json")
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found at {config_file}")

    model = build_model(config_file, download=False)
    return model
