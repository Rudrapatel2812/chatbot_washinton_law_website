import json

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.db.queries import fetch_conversations, fetch_messages
from app.db.supabase_client import Database


router = APIRouter(tags=["history"])


@router.get("/history/{session_id}")
async def get_conversations(session_id: str) -> dict:
    settings = get_settings()
    database = Database(settings)
    try:
        async with database.acquire() as connection:
            rows = await fetch_conversations(connection, session_id)
        return {
            "conversations": [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat(),
                }
                for row in rows
            ]
        }
    finally:
        await database.close()


@router.get("/history/{session_id}/{conversation_id}")
async def get_messages(session_id: str, conversation_id: str) -> dict:
    settings = get_settings()
    database = Database(settings)
    try:
        async with database.acquire() as connection:
            rows = await fetch_messages(connection, conversation_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": str(row["id"]),
                    "role": row["role"],
                    "content": row["content"],
                    "citations": json.loads(row["citations"]) if isinstance(row["citations"], str) else (row["citations"] or []),
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ],
        }
    finally:
        await database.close()
