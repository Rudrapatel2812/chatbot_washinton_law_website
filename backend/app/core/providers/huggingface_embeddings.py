class HuggingFaceEmbeddingProvider:
    """Placeholder for a local or hosted Hugging Face embedding implementation."""

    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return 384

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Install a Hugging Face runtime before using this provider.")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Install a Hugging Face runtime before using this provider.")
