from typing import Protocol

from app.models.chat import Answer
from app.models.law import RetrievedLaw


class LLMProvider(Protocol):
    @property
    def model(self) -> str:
        ...

    async def generate_answer(
        self,
        question: str,
        laws: list[RetrievedLaw],
        history: list[dict] | None = None,
    ) -> Answer:
        ...
