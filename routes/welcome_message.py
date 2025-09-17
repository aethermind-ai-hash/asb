from fastapi import APIRouter, Request
from db import save_welcome_message_to_db  # import the function from db.py

router = APIRouter()

@router.post("/save_welcome_message")
async def save_welcome_message(request: Request):
    data = await request.json()
    client_id = data.get("client_id")
    message = data.get("message")

    if not client_id or message is None:
        return {"success": False, "error": "Missing client_id or message"}

    try:
        save_welcome_message_to_db(client_id, message)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
