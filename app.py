# app.py
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from faq_operations import create_table, get_all_faqs, add_faq, update_faq, delete_faq

app = Flask(__name__)

# Path to SQLite DB
DB_PATH = "db.sqlite"

# Create FAQ table if it doesn't exist
create_table()


# -------------------------
# Admin Panel
# -------------------------
@app.route('/')
def admin_panel():
    faqs = get_all_faqs()
    return render_template("admin.html", faqs=faqs)


# -------------------------
# FAQ Routes
# -------------------------
@app.route('/add_faq', methods=['POST'])
def add_faq_route():
    data = request.json
    add_faq(data['question'], data['answer'], data.get('popular', False))
    return jsonify({"success": True})


@app.route('/update_faq', methods=['POST'])
def update_faq_route():
    data = request.json
    update_faq(data['id'], data['question'], data['answer'], data.get('popular', False))
    return jsonify({"success": True})


@app.route('/delete_faq', methods=['POST'])
def delete_faq_route():
    data = request.json
    delete_faq(data['id'])
    return jsonify({"success": True})


# -------------------------
# Analytics Routes
# -------------------------
@app.route("/analytics/data")
def get_analytics():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"error": "Missing client_id"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Only select customer interactions
        cur.execute("""
            SELECT event_type, timestamp
            FROM analytics
            WHERE client_id=? AND source='customer'
        """, (int(client_id),))
        rows = cur.fetchall()

    finally:
        conn.close()

    total_interactions = len(rows)
    faq_used = sum(1 for r in rows if r["event_type"] == "faq_click")
    ai_used = sum(1 for r in rows if r["event_type"] == "ai_request")
    new_leads = sum(1 for r in rows if r["event_type"] == "new_lead")

    # For chart: count events per day
    chart_data = {}
    for r in rows:
        date = r["timestamp"].split("T")[0]
        if date not in chart_data:
            chart_data[date] = {"faq_click": 0, "ai_request": 0}
        if r["event_type"] in chart_data[date]:
            chart_data[date][r["event_type"]] += 1

    labels = sorted(chart_data.keys())
    faq_usage = [chart_data[d]["faq_click"] for d in labels]
    ai_requests = [chart_data[d]["ai_request"] for d in labels]

    return jsonify({
        "totalInteractions": total_interactions,
        "activeUsers": 1,  # optionally calculate unique user count
        "faqUsed": faq_used,
        "faqTotal": faq_used,  # or total FAQs in DB
        "newLeads": new_leads,
        "aiUsed": ai_used,
        "aiTotal": ai_used,
        "labels": labels,
        "faqUsage": faq_usage,
        "aiRequests": ai_requests
    })


# -------------------------
# Analytics Logging Route
# -------------------------
@app.route("/analytics/log_event", methods=["POST"])
def log_event():
    data = request.json
    client_id = data.get("client_id")
    event_type = data.get("event_type")
    event_data = data.get("data", {})
    timestamp = data.get("timestamp")
    source = event_data.get("source", "customer")  # default to customer

    if not client_id or not event_type or not timestamp:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"error": "Invalid client_id"}), 400

    event_data_str = json.dumps(event_data)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO analytics (client_id, event_type, data, timestamp, source)
            VALUES (?, ?, ?, ?, ?)
        """, (client_id, event_type, event_data_str, timestamp, source))
        conn.commit()
    except Exception as e:
        print("Analytics insert error:", e)
        return jsonify({"error": "Failed to log event"}), 500
    finally:
        conn.close()

    return jsonify({"success": True})


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
