from fastapi import FastAPI, Request, Form, HTTPException, status, Depends, Query, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import sqlite3
import os
import logging
from rapidfuzz import process, fuzz
from datetime import datetime
import json
from routes import welcome_message




# ----------------------------
# IMPORT ROUTES
# ----------------------------
from routes import analytics, faqs

# ----------------------------
# CREATE APP
# ----------------------------
load_dotenv()
app = FastAPI()

router = APIRouter()

# ----------------------------
# INCLUDE ROUTERS
# ----------------------------
app.include_router(analytics.router)
app.include_router(faqs.router, prefix="/faqs")
app.include_router(router)
app.include_router(welcome_message.router)


# ----------------------------
# STATIC FILES & TEMPLATES
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# ----------------------------
# ADMIN PASSWORD
# ----------------------------
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ----------------------------
# SESSION MIDDLEWARE
# ----------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change_this_secret_for_prod"),
    session_cookie="session",
    https_only=os.getenv("ENV") == "production"
)

# ----------------------------
# DATABASE UTILITIES
# ----------------------------
from db import (
    get_db,
    get_db_connection,
    init_all_db,
    read_faq,
    add_client,
    is_client,
    get_client_id,
    add_or_update_user_integration,
    delete_faq_in_db,
    log_audit,
    get_faq_count
)
from models_utils import load_client_model  # client-specific AI model loader

# ----------------------------
# CLIENT MODEL CACHE
# ----------------------------
client_models = {}  # {client_id: model_instance}


# ----------------------------
# CONFIG / SETUP
# ----------------------------
load_dotenv()

# Include routers (analytics, faqs, custom endpoints)
from routes import analytics, faqs
app.include_router(analytics.router)
app.include_router(faqs.router, prefix="/faqs")
app.include_router(router)

# Static files and templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Admin password
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change_this_secret_for_prod"),
    session_cookie="session",
    https_only=os.getenv("ENV") == "production"
)

# Database
DB_FILE = os.getenv("DB_FILE", r"D:\ai-support-bot\ai-support-bot.db")
init_all_db()

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ----------------------------
# GOOGLE OAUTH
# ----------------------------
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
    redirect_uri="http://127.0.0.1:8000/auth/google/callback"
)

@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        resp = await oauth.google.get("https://www.googleapis.com/oauth2/v2/userinfo", token=token)
        user_info = resp.json()
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture") or "/static/default_avatar.png"

        if not email:
            raise HTTPException(status_code=400, detail="Google login failed: no email returned")

        if not is_client(email):
            add_client(email, name, picture)

        request.session["user"] = {"email": email, "name": name, "picture": picture}
        client_id = get_client_id(email)
        request.session["client_id"] = client_id

        return RedirectResponse(url="/dashboard")
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return RedirectResponse(url="/login")

# ----------------------------
# DASHBOARD
# ----------------------------
@app.get("/dashboard")
def dashboard(request: Request, conn: sqlite3.Connection = Depends(get_db)):
    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        request.session.pop("user", None)
        return RedirectResponse(url="/login")

    client_id = get_client_id(user["email"])
    if not client_id:
        request.session.pop("user", None)
        return RedirectResponse(url="/login")

    faq = read_faq(client_id)
    row = conn.execute("SELECT integration_code FROM client_integrations WHERE client_id=?", (client_id,)).fetchone()
    integration_code = row["integration_code"] if row and row["integration_code"] else "<script src='/static/script.js'></script>"
    if not row:
        add_or_update_user_integration(user["email"], integration_code, conn)

    display_name = user.get("name") or user["email"].split("@")[0]
    display_picture = user.get("picture") or "/static/default_avatar.png"

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": {
                "name": display_name,
                "email": user["email"],
                "picture": display_picture,
                "client_id": client_id
            },
            "integration_code": integration_code,
            "faq": faq
        }
    )

# ----------------------------
# FAQ / Welcome Message
# ----------------------------
@app.get("/faq_data")
async def faq_data():
    conn = get_db_connection()
    cursor = conn.execute("SELECT question, answer, popular FROM faqs ORDER BY popular DESC, id ASC")
    faqs = {row["question"]: {"answer": row["answer"], "popular": bool(row["popular"])} for row in cursor.fetchall()}
    popular_faqs = {q: faqs[q] for q in faqs if faqs[q]["popular"]}
    conn.close()
    return {"all": faqs, "popular": popular_faqs}

@app.post("/update_faq")
async def update_faq(request: Request):
    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        raise HTTPException(status_code=403, detail="Unauthorized")

    data = await request.json()
    client_id = get_client_id(user["email"])
    question = str(data.get("question", "")).strip()
    answer = str(data.get("answer", "")).strip()
    popular = int(data.get("popular", 0))

    if not question or not answer:
        raise HTTPException(status_code=400, detail="Missing required fields")

    conn = sqlite3.connect(DB_FILE, timeout=30, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            conn.execute("""
                INSERT INTO faqs (client_id, question, answer, popular)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(client_id, question) DO UPDATE SET
                    answer=excluded.answer,
                    popular=excluded.popular
            """, (client_id, question, answer, popular))
    finally:
        conn.close()

    return {"success": True, "message": "FAQ saved successfully"}


@app.post("/delete_faq")
def delete_faq(request: Request, question: str = Form(...)):
    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        raise HTTPException(status_code=403, detail="Unauthorized")
    delete_faq_in_db(get_client_id(user["email"]), question)
    return {"success": True}

@app.get("/welcome_message")
def get_welcome_message(request: Request):
    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = get_db_connection()
    client_id = get_client_id(user["email"], conn)
    row = conn.execute("SELECT message FROM welcome_messages WHERE client_id=?", (client_id,)).fetchone()
    conn.close()
    return {"message": row["message"] if row else "Hello! How can I assist you today?"}

@app.post("/update_welcome_message")
def update_welcome_message(request: Request, message: str = Form(...)):
    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = get_db_connection()
    client_id = get_client_id(user["email"], conn)
    existing = conn.execute("SELECT id FROM welcome_messages WHERE client_id=?", (client_id,)).fetchone()
    if existing:
        conn.execute("UPDATE welcome_messages SET message=? WHERE id=?", (message, existing["id"]))
        action = "Updated welcome message"
    else:
        conn.execute("INSERT INTO welcome_messages (client_id, message) VALUES (?, ?)", (client_id, message))
        action = "Added welcome message"
    conn.commit()
    conn.close()
    log_audit(client_id, action, performed_by=user["email"])
    return {"success": True}

@app.post("/update_integration")
def update_integration(request: Request, code: str = Form(...)):
    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        raise HTTPException(status_code=403, detail="Unauthorized")
    add_or_update_user_integration(user["email"], code)
    return {"success": True, "message": "Integration code saved."}

# ----------------------------
# Chatbot (FAQ + AI)
# ----------------------------
MAX_FAQ_MATCH_SCORE = 65

def log_analytics_event(client_id, event_type, details="", user_id=None, source="customer"):
    conn = get_db_connection()
    ts = datetime.utcnow().isoformat()
    try:
        conn.execute("""
            INSERT INTO analytics (client_id, user_id, event_type, details, timestamp, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (client_id, user_id, event_type, json.dumps(details), ts, source))
        conn.commit()
    finally:
        conn.close()

@app.post("/chatbot_message")
async def chatbot_message(request: Request):
    data = await request.json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return JSONResponse({"reply": "Please type a message."})

    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        raise HTTPException(status_code=403, detail="Unauthorized")
    client_id = get_client_id(user["email"])

    # Load FAQs
    conn = get_db_connection()
    cursor = conn.execute("SELECT question, answer FROM faqs WHERE client_id=?", (client_id,))
    faqs = {row["question"]: row["answer"] for row in cursor.fetchall()}
    conn.close()

    bot_reply = None
    source = None

    # FAQ fuzzy match
    if faqs:
        best_match = process.extractOne(user_msg, list(faqs.keys()), scorer=fuzz.token_sort_ratio)
        if best_match and best_match[1] < MAX_FAQ_MATCH_SCORE:
            best_match = process.extractOne(user_msg, list(faqs.keys()), scorer=fuzz.partial_ratio)
        if best_match and best_match[1] >= MAX_FAQ_MATCH_SCORE:
            bot_reply = faqs[best_match[0]]
            source = "faq"

    # AI fallback
    if not bot_reply:
        try:
            model = load_client_model(client_id)
            bot_reply = model([user_msg])[0]
            source = "ai"
        except Exception as e:
            bot_reply = f"Error processing message: {str(e)}"
            source = "error"

    # Log analytics
    details = {"message": user_msg}
    if source == "faq":
        details["matched_question"] = best_match[0]
    log_analytics_event(client_id, f"chatbot_{source}", details, user_id=user.get("email"))

    return JSONResponse({"reply": bot_reply, "source": source})

# ----------------------------
# Landing & Index
# ----------------------------
@app.get("/landing")
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/")
def index(request: Request):
    user = request.session.get("user")
    faq = read_faq(get_client_id(user["email"])) if user else read_faq()
    popular_questions = [q for q, i in faq.items() if i.get("popular")]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "faq": faq, "popular_questions": popular_questions, "user": user}
    )

# ----------------------------
# Profile & Logout
# ----------------------------
@app.post("/update_profile")
async def update_profile(request: Request, name: str = Form(...), email: str = Form(...), company: str = Form(""), role: str = Form("")):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")
    conn = get_db_connection()
    conn.execute("UPDATE clients SET name=?, email=?, company=?, role=? WHERE email=?", (name, email, company, role, user["email"]))
    conn.commit()
    conn.close()
    request.session["user"].update({"name": name, "email": email, "company": company, "role": role})
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/user_logout")
async def user_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")

# ----------------------------
# Admin
# ----------------------------
@app.get("/admin_login")
def admin_login_get(request: Request, detail: str = None):
    return templates.TemplateResponse("admin_login.html", {"request": request, "detail": detail})

@app.post("/admin_login")
def admin_login_post(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["admin_logged_in"] = True
        log_audit(None, "Admin logged in", performed_by="admin")
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin_login.html", {"request": request, "detail": "Invalid password"})

@app.get("/admin")
def admin_page(request: Request):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin_login")
    faq = read_faq()
    return templates.TemplateResponse("admin.html", {"request": request, "faq": faq})

@app.get("/logout")
def admin_logout(request: Request):
    user_email = request.session.get("user", {}).get("email")
    if user_email:
        log_audit(get_client_id(user_email), "Client logged out", performed_by=user_email)
    request.session.clear()
    return RedirectResponse(url="/admin_login")

@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse("client_login.html", {"request": request})

# ----------------------------
# Analytics Logging Endpoint
# ----------------------------
@app.post("/analytics/log_event")
async def log_event(request: Request):
    user = request.session.get("user")
    if not user or not is_client(user.get("email")):
        raise HTTPException(status_code=403, detail="Unauthorized")

    data = await request.json()
    event_type = data.get("event_type")
    details = data.get("details", "")
    if not event_type:
        raise HTTPException(status_code=400, detail="Missing event_type")

    client_id = get_client_id(user["email"])
    log_analytics_event(client_id, event_type, details, user_id=user.get("email"))
    return {"success": True, "message": f"Logged event '{event_type}' for client {client_id}"}

# ----------------------------
# Client FAQ Usage
# ----------------------------
@router.get("/analytics/faq_usage")
def faq_usage(client_id: int = Query(..., description="Client ID")):
    if not client_id:
        raise HTTPException(status_code=400, detail="Missing client_id")
    count = get_faq_count(client_id=client_id)
    return {"count": count}
