from __future__ import annotations

import logging

from app.core.embeddings import EmbeddingProvider
from app.db.queries import fetch_laws_without_embeddings, insert_law_embedding
from app.db.supabase_client import Database


logger = logging.getLogger(__name__)

BATCH_SIZE = 50
MAX_CHARS = 30_000


def _build_text(citation: str, heading: str | None, text: str) -> str:
    parts = [citation]
    if heading:
        parts.append(heading)
    parts.append(text)
    combined = " ".join(parts)
    return combined[:MAX_CHARS]


async def embed_all(database: Database, provider: EmbeddingProvider) -> int:
    total = 0
    async with database.acquire() as connection:
        rows = await fetch_laws_without_embeddings(connection, "openai", provider.model)

    if not rows:
        logger.info("embed_all status=already_complete")
        return 0

    logger.info("embed_all pending=%s", len(rows))

    for batch_start in range(0, len(rows), BATCH_SIZE):
        batch = rows[batch_start : batch_start + BATCH_SIZE]
        texts = [_build_text(r["citation"], r["heading"], r["text"]) for r in batch]
        embeddings = await provider.embed_batch(texts)

        async with database.acquire() as connection:
            async with connection.transaction():
                for row, embedding in zip(batch, embeddings):
                    await insert_law_embedding(
                        connection,
                        law_id=str(row["id"]),
                        provider="openai",
                        model=provider.model,
                        dimensions=provider.dimensions,
                        embedding=embedding,
                    )

        total += len(batch)
        logger.info("embed_all progress=%s/%s", total, len(rows))

    return total
