import openai
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.prompts import ANSWER_PROMPT_V1
from app.models.chat import Answer, Citation
from app.models.law import RetrievedLaw

_RETRYABLE = (openai.APIConnectionError, openai.APITimeoutError, openai.InternalServerError)


class OpenAILLMProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=30.0)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate_answer(
        self,
        question: str,
        laws: list[RetrievedLaw],
        history: list[dict] | None = None,
    ) -> Answer:
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

        messages: list[dict] = [{"role": "system", "content": ANSWER_PROMPT_V1}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": f"Question: {question}\n\nLaw excerpts:\n{context}"})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
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
