from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse
import sqlite3
from datetime import datetime
import json
from db import get_db_connection, get_faq_count, get_ai_request_count, get_user_plan

router = APIRouter()


# ----------------------------
# LOG ANALYTICS EVENT
# ----------------------------
@router.post("/analytics/log")
async def log_event(request: Request):
    data = await request.json()

    # Here, get client_id from session, JWT, or request (instead of sending it manually)
    client_id = data.get("client_id")  # replace this with session/client auth in production
    user_id = data.get("user_id") or "anonymous"
    source = data.get("source") or "customer"
    event_type = data.get("event_type")
    details = data.get("details") or {}
    extra_data = data.get("data") or {}

    if not client_id or not event_type:
        raise HTTPException(status_code=400, detail="Missing required fields")

    ts = datetime.utcnow().isoformat()
    details_json = json.dumps(details)
    data_json = json.dumps(extra_data)

    # Skip admin events
    if source != "customer":
        return {"status": "ignored", "reason": "admin event not logged"}

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO analytics (client_id, user_id, source, event_type, data, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (int(client_id), user_id, source, event_type, data_json, details_json, ts)
        )
        conn.commit()
    finally:
        conn.close()

    return {"status": "success", "message": "Event logged"}

# ----------------------------
# GET ANALYTICS DATA
# ----------------------------

# ----------------------------
# GET ANALYTICS DATA (MVP version)
# ----------------------------
@router.get("/analytics/data")
def get_analytics(client_id: int = Query(...)):
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")
    
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        
        # Total interactions
        cur.execute("SELECT COUNT(*) as total FROM analytics WHERE client_id=?", (client_id,))
        total_interactions = cur.fetchone()["total"] or 0

        # Active users last 30 days
        cur.execute("""
            SELECT COUNT(DISTINCT user_id) as users
            FROM analytics
            WHERE client_id=? AND datetime(timestamp) >= datetime('now', '-30 days')
        """, (client_id,))
        active_users = cur.fetchone()["users"] or 0

        # ------------------------
        # FAQ limit (MVP)
        # ------------------------
        # For MVP, define a simple fixed limit per client
        faq_limit_per_client = 50  # change as needed
        # Count actual FAQs created by the client
        cur.execute("SELECT COUNT(*) as created FROM faqs WHERE client_id=?", (client_id,))
        faq_created = cur.fetchone()["created"] or 0

        # AI usage
        used_ai = get_ai_request_count(client_id)
        plan = (get_user_plan(client_id) or "demo").lower()
        ai_limits = {"demo": 100, "onetime": 500, "basic": 1000, "standard": 5000, "premium": float('inf')}
        max_ai = ai_limits.get(plan, 100)
        remaining_ai = max_ai - used_ai if max_ai != float('inf') else float('inf')

        # Daily counts
        cur.execute("""
            SELECT DATE(timestamp) as day,
                   SUM(CASE WHEN event_type='faq_click' THEN 1 ELSE 0 END) as faq_count,
                   SUM(CASE WHEN event_type='ai_request' THEN 1 ELSE 0 END) as ai_count
            FROM analytics
            WHERE client_id=? AND datetime(timestamp) >= datetime('now', '-30 days')
            GROUP BY day
            ORDER BY day
        """, (client_id,))
        rows = cur.fetchall()
        daily_labels = [r["day"] for r in rows]
        daily_faq_counts = [r["faq_count"] for r in rows]
        daily_ai_counts = [r["ai_count"] for r in rows]

        # Raw events
        cur.execute("SELECT event_type, details, timestamp FROM analytics WHERE client_id=? ORDER BY timestamp ASC", (client_id,))
        events = [{"event_type": r["event_type"], "details": r["details"], "timestamp": r["timestamp"]} for r in cur.fetchall()]

    finally:
        conn.close()

    return JSONResponse({
        "total_interactions": total_interactions,
        "active_users": active_users,
        "faq_usage": {"created": faq_created, "limit": faq_limit_per_client},
        "remaining_ai_requests": {"used": used_ai, "limit": remaining_ai},
        "daily": {"labels": daily_labels, "faq_counts": daily_faq_counts, "ai_counts": daily_ai_counts},
        "events": events
    })
