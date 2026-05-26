from app.db.supabase_client import Database
from app.core.embeddings import EmbeddingProvider
from app.core.llm import LLMProvider

_database: Database | None = None
_embedding_provider: EmbeddingProvider | None = None
_llm_provider: LLMProvider | None = None


def get_database() -> Database:
    if _database is None:
        raise RuntimeError("Database not initialized. App may not have started correctly.")
    return _database


def get_embedding_provider() -> EmbeddingProvider:
    if _embedding_provider is None:
        raise RuntimeError("Embedding provider not initialized.")
    return _embedding_provider


def get_llm_provider() -> LLMProvider:
    if _llm_provider is None:
        raise RuntimeError("LLM provider not initialized.")
    return _llm_provider
