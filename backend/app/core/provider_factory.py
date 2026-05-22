from app.config import Settings
from app.core.embeddings import EmbeddingProvider
from app.core.llm import LLMProvider
from app.core.providers.fallback_llm import ExtractiveLLMProvider
from app.core.providers.huggingface_embeddings import HuggingFaceEmbeddingProvider
from app.core.providers.openai_embeddings import OpenAIEmbeddingProvider
from app.core.providers.openai_llm import OpenAILLMProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings.")
        return OpenAIEmbeddingProvider(settings.openai_api_key, settings.embedding_model)
    if settings.embedding_provider == "huggingface":
        return HuggingFaceEmbeddingProvider(settings.embedding_model)
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAILLMProvider(settings.openai_api_key, settings.llm_model)
    return ExtractiveLLMProvider()
