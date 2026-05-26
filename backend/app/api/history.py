import json

from fastapi import APIRouter, Depends, HTTPException

from app.db.queries import fetch_conversations, fetch_messages_for_session
from app.db.supabase_client import Database
from app.dependencies import get_database

router = APIRouter(tags=["history"])


@router.get("/history/{session_id}")
async def get_conversations(
    session_id: str,
    database: Database = Depends(get_database),
) -> dict:
    async with database.acquire() as conn:
        rows = await fetch_conversations(conn, session_id)
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


@router.get("/history/{session_id}/{conversation_id}")
async def get_messages(
    session_id: str,
    conversation_id: str,
    database: Database = Depends(get_database),
) -> dict:
    async with database.acquire() as conn:
        # Ownership enforced in query — only returns rows if conversation belongs to session
        rows = await fetch_messages_for_session(conn, conversation_id, session_id)
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
