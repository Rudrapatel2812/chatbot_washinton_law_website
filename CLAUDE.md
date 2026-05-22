# Washington Legal Chatbot

This project is a production-grade portfolio build for a Washington State legal AI chatbot.

Core principle: answers must be grounded in retrieved law text and cited to specific RCW sections. If the system cannot retrieve relevant law, it should say it does not know instead of guessing.

## Locked Stack

- Python 3.11+
- FastAPI backend
- Supabase PostgreSQL with pgvector
- Supabase Auth
- httpx, BeautifulSoup, tenacity, aiolimiter for the scraper
- structlog for JSON logging
- Pydantic v2 for validation
- Pluggable embedding and LLM providers

## Build Order

1. Foundation: schema, settings, connection checks
2. Data pipeline: raw HTML, parsed JSON, database load
3. Embeddings and retrieval
4. API, auth, history
5. Frontend
6. Polish and deploy

## Development Rules

- Do not store secrets in code.
- Keep raw HTML, parsed JSON, and database loading as separate rerunnable stages.
- Use Pydantic models at module boundaries.
- Use parameterized SQL only.
- No generated answer should cite a law section that was not retrieved.
- Preserve legal source text and citations exactly enough to audit answers.
