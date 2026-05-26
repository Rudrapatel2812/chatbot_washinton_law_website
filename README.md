# Washington State Legal Assistant

> Built by [Rudra Patel](https://github.com/Rudrapatel2812)

An AI-powered legal research tool grounded in Washington State Revised Code (RCW). Answers are generated strictly from retrieved law text and cite the exact RCW section — if the system cannot find relevant law, it says so rather than guessing.

**Live:** https://chatbot-washinton-law-website.vercel.app  
**API:** https://chatbot-washinton-law-website.onrender.com

---

## Architecture

```
User question
     │
     ▼
OpenAI text-embedding-3-small
     │
     ▼
pgvector cosine similarity search  ──  score > 0.4 threshold
     │                                         │
     ▼                                         ▼
GPT-4o-mini (strict grounding prompt)    "I don't know"
+ last 3 conversation turns
     │
     ▼
Answer + RCW citations → saved to Supabase
```

The model is not allowed to answer from general knowledge. If the retrieved sections don't support an answer, the response is "I don't know based on the retrieved Washington law."

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11, asyncpg |
| Database | Supabase PostgreSQL + pgvector |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-4o-mini` |
| Hosting | Vercel + Render |
| Rate limiting | slowapi — 15 req/min per IP |
| Retries | tenacity — exponential backoff on transient errors |

---

## RCW Coverage

20 titles, 12,000+ sections with vector embeddings.

| Titles | Domain |
|---|---|
| 9, 9A, 10 | Criminal law, criminal procedure |
| 26, 46, 59 | Family, motor vehicles, landlord-tenant |
| 11, 13, 48, 49 | Probate, juvenile courts, insurance, labor |
| 50, 51, 64 | Unemployment, workers' comp, real property |
| 1, 19, 70, 71, 74 | General law, business, public health, behavioral health, public assistance |

---

## Sample Questions

1. What is assault in the fourth degree in Washington?
2. How is child custody decided in Washington State?
3. Can a landlord keep my security deposit in Washington?
4. What is the DUI blood alcohol limit in Washington?
5. Who is prohibited from owning a firearm in Washington?
6. How does Washington calculate child support?
7. What injuries are covered by workers' compensation in Washington?
8. What happens to property when someone dies without a will in Washington?
9. What protections do whistleblowers have under Washington law?
10. What does RCW 9A.36.041 say?

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes (chat, history)
│   │   ├── core/             # Embeddings, LLM, retrieval, prompts
│   │   │   └── providers/    # Pluggable OpenAI implementations
│   │   ├── db/               # asyncpg client, parameterized SQL queries
│   │   ├── models/           # Pydantic v2 models
│   │   ├── dependencies.py   # Singleton provider injection via FastAPI Depends
│   │   ├── limiter.py        # slowapi rate limiter
│   │   └── main.py           # Lifespan, middleware, CORS, rate limit handler
│   └── data_pipeline/        # Scraper → parser → loader → embedder (rerunnable stages)
├── database/
│   ├── 01_schema.sql         # laws, law_embeddings, conversations, messages
│   ├── 02_indexes.sql        # pgvector ivfflat, covering indexes
│   └── 03_rls_policies.sql   # Row-level security
├── frontend/
│   └── app/
│       ├── ChatApp.tsx       # Chat UI with session management
│       └── globals.css       # Animations, iOS safe-area, mobile layout
└── render.yaml               # Render deployment config
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/api/query` | Submit a question |
| `GET` | `/api/history/{session_id}` | List conversations |
| `GET` | `/api/history/{session_id}/{conv_id}` | Load messages |

**POST /api/query**

```bash
curl -X POST https://chatbot-washinton-law-website.onrender.com/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is assault in the fourth degree?", "session_id": "abc123"}'
```

```json
{
  "answer": "Under RCW 9A.36.041, a person is guilty of assault in the fourth degree...",
  "citations": [
    {
      "citation": "RCW 9A.36.041",
      "source_url": "https://app.leg.wa.gov/rcw/default.aspx?cite=9A.36.041",
      "excerpt": "A person is guilty of assault in the fourth degree..."
    }
  ],
  "confidence": "medium",
  "conversation_id": "uuid"
}
```

---

## Running Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project with pgvector enabled
- OpenAI API key

### Setup

```bash
git clone <repo-url>
cd chatbot_washinton_law_website-main
cp .env.example backend/.env
# fill in backend/.env (see Environment Variables below)
```

**Database:** Run the following in Supabase SQL Editor in order:

```
database/01_schema.sql
database/02_indexes.sql
database/03_rls_policies.sql
```

Then drop the unused auth foreign key:

```sql
ALTER TABLE conversations DROP CONSTRAINT conversations_user_id_fkey;
```

**Data pipeline:**

```bash
cd backend
pip install -r requirements.txt

python -m data_pipeline.run scrape --titles 9 9A 26 46 59
python -m data_pipeline.run parse  --titles 9 9A 26 46 59
python -m data_pipeline.run load   --titles 9 9A 26 46 59
python -m data_pipeline.run embed
```

**Start services:**

```bash
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

---

## Deployment

**Backend (Render):** `render.yaml` is pre-configured. Set env vars in the dashboard. Use the Supabase Connection Pooler URL (port 6543, transaction mode) for `DATABASE_URL` — the direct URL is IPv6-only and will fail on Render.

**Frontend (Vercel):** Set Root Directory to `frontend`. Add `NEXT_PUBLIC_API_URL` pointing to your Render URL. Redeploy after setting it (baked in at build time).

### Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase pooler URL — port 6543 |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `OPENAI_API_KEY` | OpenAI API key |
| `ALLOWED_ORIGINS` | Comma-separated allowed frontend origins |
| `NEXT_PUBLIC_API_URL` | Backend URL (frontend, build-time) |

---

## Legal Disclaimer

This tool provides legal information, not legal advice. Answers are derived from retrieved RCW text and may be incomplete or out of date. Consult a licensed Washington State attorney for advice specific to your situation.
