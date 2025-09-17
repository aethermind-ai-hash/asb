# routes/faqs.py
from fastapi import APIRouter, Request, HTTPException
from db import get_db_connection, get_db

router = APIRouter()

# -------------------------
# GET ALL FAQs (return with id)
# -------------------------

@router.get("/faq_data")
async def faq_data(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from db import get_client_id
    client_id = get_client_id(user["email"])

    conn = get_db_connection()
    faqs = conn.execute("SELECT id, question, answer, popular FROM faqs WHERE client_id = ?", (client_id,)).fetchall()
    conn.close()

    # Return id too
    all_faqs = {
        row["question"]: {
            "id": row["id"],
            "answer": row["answer"],
            "popular": row["popular"]
        }
        for row in faqs
    }

    popular_faqs = {q: a for q, a in all_faqs.items() if a["popular"]}

    return {"all": all_faqs, "popular": popular_faqs}


# -------------------------
# DELETE FAQ (by id)
# -------------------------
@router.post("/delete_faq")
async def delete_faq_endpoint(request: Request):
    data = {}

    # Try JSON first
    try:
        data = await request.json()
    except Exception:
        pass

    # If JSON failed, try form
    if not data:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            return {"success": False, "error": "Invalid request data"}

    client_id = data.get("client_id")
    faq_id = data.get("faq_id")

    if not client_id or not faq_id:
        return {"success": False, "error": "Missing client_id or faq_id"}

    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM faqs WHERE client_id=? AND id=?", (client_id, faq_id))
            conn.commit()

            # Optional: audit logs
            action = f"Deleted FAQ ID: {faq_id}"
            conn.execute(
                "INSERT INTO audit_logs (client_id, action, performed_by) VALUES (?, ?, ?)",
                (client_id, action, None)
            )
            conn.commit()

        return {"success": True, "message": f"FAQ ID {faq_id} deleted successfully"}
    except Exception as e:
        print("Error deleting FAQ:", e)
        return {"success": False, "error": str(e)}

# -------------------------
# ADD OR UPDATE FAQ
# -------------------------
@router.post("/update_faq")
async def update_faq(request: Request):
    data = {}

    # Try JSON first
    try:
        data = await request.json()
    except Exception:
        pass

    # If JSON failed, try form
    if not data:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request data")

    client_id = data.get("client_id")
    question = data.get("question")
    answer = data.get("answer")
    popular = int(data.get("popular", 0))

    if not client_id or not question or not answer:
        raise HTTPException(status_code=400, detail="Missing fields")

    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT id FROM faqs WHERE client_id=? AND question=?",
                (client_id, question)
            ).fetchone()

            if row:
                conn.execute(
                    "UPDATE faqs SET answer=?, popular=? WHERE id=?",
                    (answer, popular, row["id"])
                )
            else:
                conn.execute(
                    "INSERT INTO faqs (client_id, question, answer, popular) VALUES (?, ?, ?, ?)",
                    (client_id, question, answer, popular)
                )
            conn.commit()

        return {"success": True, "message": "FAQ saved successfully!"}
    except Exception as e:
        print("Error in /update_faq:", e)
        raise HTTPException(status_code=500, detail=str(e))
