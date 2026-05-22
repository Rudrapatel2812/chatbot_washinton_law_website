from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.core.provider_factory import build_embedding_provider, build_llm_provider
from app.core.retrieval import LawRetriever
from app.db.queries import create_conversation, save_message
from app.db.supabase_client import Database
from app.models.chat import Answer, QueryRequest


router = APIRouter(tags=["chat"])


@router.post("/query", response_model=Answer)
async def query(request: QueryRequest) -> Answer:
    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    database = Database(settings)
    try:
        embedding_provider = build_embedding_provider(settings)
        llm_provider = build_llm_provider(settings)
        retriever = LawRetriever(database, embedding_provider)
        retrieved_laws = await retriever.retrieve(request.question, request.jurisdiction_code)
        answer = await llm_provider.generate_answer(request.question, retrieved_laws)

        if request.session_id:
            async with database.acquire() as connection:
                conversation_id = request.conversation_id
                if not conversation_id:
                    title = request.question[:60]
                    conversation_id = await create_conversation(connection, request.session_id, title)
                await save_message(connection, conversation_id, "user", request.question)
                await save_message(
                    connection,
                    conversation_id,
                    "assistant",
                    answer.answer,
                    [c.model_dump() for c in answer.citations],
                )
                answer.conversation_id = conversation_id

        return answer
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        await database.close()
