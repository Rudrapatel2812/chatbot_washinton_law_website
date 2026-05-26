import json

import asyncpg

from app.models.law import Law, LawStatus, RetrievedLaw


WA_JURISDICTION_CODE = "WA"


def _record_to_law(record: asyncpg.Record) -> Law:
    values = dict(record)
    return Law(
        id=str(record["id"]),
        jurisdiction_id=str(record["jurisdiction_id"]),
        jurisdiction_code=values.get("jurisdiction_code", "WA"),
        citation=record["citation"],
        title_number=record["title_number"],
        chapter_number=record["chapter_number"],
        section_number=record["section_number"],
        heading=record["heading"],
        text=record["text"],
        source_url=record["source_url"],
        status=LawStatus(record["status"]),
    )


async def fetch_law_by_citation(
    connection: asyncpg.Connection,
    jurisdiction_code: str,
    citation: str,
) -> Law | None:
    record = await connection.fetchrow(
        """
        SELECT laws.*, jurisdictions.code AS jurisdiction_code
        FROM laws
        JOIN jurisdictions ON jurisdictions.id = laws.jurisdiction_id
        WHERE jurisdictions.code = $1
          AND laws.citation = $2
        LIMIT 1
        """,
        jurisdiction_code,
        citation,
    )
    return _record_to_law(record) if record else None


async def fetch_jurisdiction_id(connection: asyncpg.Connection, code: str) -> str:
    jurisdiction_id = await connection.fetchval(
        "SELECT id FROM jurisdictions WHERE code = $1",
        code,
    )
    if not jurisdiction_id:
        raise ValueError(f"Unknown jurisdiction code: {code}")
    return str(jurisdiction_id)


async def semantic_search_laws(
    connection: asyncpg.Connection,
    jurisdiction_code: str,
    embedding_model: str,
    query_embedding: list[float],
    limit: int = 5,
) -> list[RetrievedLaw]:
    vector_literal = "[" + ",".join(str(value) for value in query_embedding) + "]"
    rows = await connection.fetch(
        """
        SELECT laws.*, jurisdictions.code AS jurisdiction_code, law_embeddings.embedding <=> $3::vector AS distance
        FROM law_embeddings
        JOIN laws ON laws.id = law_embeddings.law_id
        JOIN jurisdictions ON jurisdictions.id = laws.jurisdiction_id
        WHERE jurisdictions.code = $1
          AND law_embeddings.model = $2
        ORDER BY law_embeddings.embedding <=> $3::vector
        LIMIT $4
        """,
        jurisdiction_code,
        embedding_model,
        vector_literal,
        limit,
    )
    return [
        RetrievedLaw(law=_record_to_law(row), score=float(row["distance"]), retrieval_method="semantic")
        for row in rows
    ]


async def fetch_laws_without_embeddings(
    connection: asyncpg.Connection,
    provider: str,
    model: str,
) -> list[asyncpg.Record]:
    return await connection.fetch(
        """
        SELECT id, citation, heading, text FROM laws
        WHERE text != ''
          AND NOT EXISTS (
            SELECT 1 FROM law_embeddings
            WHERE law_id = laws.id AND provider = $1 AND model = $2
          )
        ORDER BY citation
        """,
        provider,
        model,
    )


async def insert_law_embedding(
    connection: asyncpg.Connection,
    law_id: str,
    provider: str,
    model: str,
    dimensions: int,
    embedding: list[float],
) -> None:
    vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"
    await connection.execute(
        """
        INSERT INTO law_embeddings (law_id, provider, model, dimensions, embedding)
        VALUES ($1, $2, $3, $4, $5::vector)
        ON CONFLICT (law_id, provider, model) DO NOTHING
        """,
        law_id,
        provider,
        model,
        dimensions,
        vector_literal,
    )


async def insert_law(connection: asyncpg.Connection, law: Law) -> str:
    jurisdiction_id = law.jurisdiction_id or await fetch_jurisdiction_id(connection, law.jurisdiction_code)
    law_id = await connection.fetchval(
        """
        INSERT INTO laws (
            jurisdiction_id, citation, title_number, chapter_number, section_number,
            heading, text, source_url, status
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (jurisdiction_id, citation)
        DO UPDATE SET
            heading = EXCLUDED.heading,
            text = EXCLUDED.text,
            source_url = EXCLUDED.source_url,
            status = EXCLUDED.status,
            updated_at = now()
        RETURNING id
        """,
        jurisdiction_id,
        law.citation,
        law.title_number,
        law.chapter_number,
        law.section_number,
        law.heading,
        law.text,
        law.source_url,
        law.status.value,
    )
    return str(law_id)


# ── History ──────────────────────────────────────────────────────────────────

async def create_conversation(connection: asyncpg.Connection, session_id: str, title: str | None = None) -> str:
    conversation_id = await connection.fetchval(
        """
        INSERT INTO conversations (user_id, title)
        VALUES ($1, $2)
        RETURNING id
        """,
        session_id,
        title,
    )
    return str(conversation_id)


async def save_message(
    connection: asyncpg.Connection,
    conversation_id: str,
    role: str,
    content: str,
    citations: list[dict] | None = None,
) -> str:
    message_id = await connection.fetchval(
        """
        INSERT INTO messages (conversation_id, role, content, citations)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        conversation_id,
        role,
        content,
        json.dumps(citations or []),
    )
    return str(message_id)


async def fetch_conversations(connection: asyncpg.Connection, session_id: str) -> list[asyncpg.Record]:
    return await connection.fetch(
        """
        SELECT id, title, created_at, updated_at
        FROM conversations
        WHERE user_id = $1
        ORDER BY updated_at DESC
        LIMIT 50
        """,
        session_id,
    )


async def fetch_messages(connection: asyncpg.Connection, conversation_id: str) -> list[asyncpg.Record]:
    return await connection.fetch(
        """
        SELECT id, role, content, citations, created_at
        FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
        """,
        conversation_id,
    )


async def fetch_messages_for_session(
    connection: asyncpg.Connection,
    conversation_id: str,
    session_id: str,
) -> list[asyncpg.Record]:
    """Fetch messages only if the conversation belongs to the given session (ownership check)."""
    return await connection.fetch(
        """
        SELECT m.id, m.role, m.content, m.citations, m.created_at
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE m.conversation_id = $1
          AND c.user_id = $2
        ORDER BY m.created_at ASC
        """,
        conversation_id,
        session_id,
    )
