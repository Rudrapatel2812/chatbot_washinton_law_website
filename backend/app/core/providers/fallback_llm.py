from app.models.chat import Answer, Citation
from app.models.law import RetrievedLaw


class ExtractiveLLMProvider:
    """A safe fallback that returns retrieved excerpts without generation."""

    @property
    def model(self) -> str:
        return "extractive-fallback-v1"

    async def generate_answer(self, question: str, laws: list[RetrievedLaw]) -> Answer:
        if not laws:
            return Answer(
                answer="I don't know based on the retrieved Washington law. This is legal information, not legal advice.",
                citations=[],
                retrieved_laws=[],
                confidence="low",
            )

        lead = laws[0].law
        answer = (
            f"The most relevant retrieved law is {lead.citation}. "
            "Review the cited source text below. This is legal information, not legal advice."
        )
        return Answer(
            answer=answer,
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
