from openai import AsyncOpenAI

from app.core.prompts import ANSWER_PROMPT_V1
from app.models.chat import Answer, Citation
from app.models.law import RetrievedLaw


class OpenAILLMProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    async def generate_answer(self, question: str, laws: list[RetrievedLaw]) -> Answer:
        if not laws:
            return Answer(
                answer="I don't know based on the retrieved Washington law. This is legal information, not legal advice.",
                citations=[],
                retrieved_laws=[],
                confidence="low",
            )

        context = "\n\n".join(
            f"{item.law.citation}\n{item.law.heading or ''}\n{item.law.text}"
            for item in laws
        )
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": ANSWER_PROMPT_V1},
                {"role": "user", "content": f"Question: {question}\n\nLaw excerpts:\n{context}"},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        return Answer(
            answer=content,
            citations=[
                Citation(
                    citation=item.law.citation,
                    source_url=item.law.source_url,
                    excerpt=item.law.text[:500],
                )
                for item in laws
            ],
            retrieved_laws=laws,
            confidence="medium",
        )
