from app.core.citations import extract_rcw_citation
from app.core.embeddings import EmbeddingProvider
from app.db.queries import fetch_law_by_citation, semantic_search_laws
from app.db.supabase_client import Database
from app.models.law import RetrievedLaw


RELEVANCE_THRESHOLD = 0.4


class LawRetriever:
    def __init__(self, database: Database, embedding_provider: EmbeddingProvider) -> None:
        self._database = database
        self._embedding_provider = embedding_provider

    async def retrieve(self, question: str, jurisdiction_code: str = "WA", limit: int = 5) -> list[RetrievedLaw]:
        async with self._database.acquire() as connection:
            citation = extract_rcw_citation(question)
            if citation:
                law = await fetch_law_by_citation(connection, jurisdiction_code, citation)
                if law:
                    return [RetrievedLaw(law=law, score=0.0, retrieval_method="direct_citation")]

            embedding = await self._embedding_provider.embed(question)
            results = await semantic_search_laws(
                connection=connection,
                jurisdiction_code=jurisdiction_code,
                embedding_model=self._embedding_provider.model,
                query_embedding=embedding,
                limit=limit,
            )
        # Discard results too dissimilar to the question — prevents hallucination from irrelevant excerpts
        return [r for r in results if r.score <= RELEVANCE_THRESHOLD]
