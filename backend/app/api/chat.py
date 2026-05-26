from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.embeddings import EmbeddingProvider
from app.core.llm import LLMProvider
from app.core.retrieval import LawRetriever
from app.db.queries import create_conversation, fetch_messages, save_message
from app.db.supabase_client import Database
from app.dependencies import get_database, get_embedding_provider, get_llm_provider
from app.limiter import limiter
from app.models.chat import Answer, QueryRequest

router = APIRouter(tags=["chat"])

# Number of prior messages passed to the LLM for conversation memory (3 turns)
_HISTORY_WINDOW = 6


@router.post("/query", response_model=Answer, response_model_exclude={"retrieved_laws"})
@limiter.limit("15/minute")
async def query(
    request: Request,
    body: QueryRequest,
    database: Database = Depends(get_database),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> Answer:
    retriever = LawRetriever(database, embedding_provider)
    retrieved_laws = await retriever.retrieve(body.question, body.jurisdiction_code)

    # Fetch recent conversation turns so the LLM has memory of this session
    history: list[dict] = []
    if body.conversation_id:
        async with database.acquire() as conn:
            rows = await fetch_messages(conn, body.conversation_id)
        history = [
            {"role": row["role"], "content": row["content"]}
            for row in rows[-_HISTORY_WINDOW:]
        ]

    try:
        answer = await llm_provider.generate_answer(body.question, retrieved_laws, history)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if body.session_id:
        async with database.acquire() as conn:
            conversation_id = body.conversation_id
            if not conversation_id:
                title = body.question[:60]
                conversation_id = await create_conversation(conn, body.session_id, title)
            await save_message(conn, conversation_id, "user", body.question)
            await save_message(
                conn,
                conversation_id,
                "assistant",
                answer.answer,
                [c.model_dump() for c in answer.citations],
            )
            answer.conversation_id = conversation_id

    return answer
