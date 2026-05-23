# Washington State Legal Assistant

An AI-powered legal research chatbot grounded in Washington State law (RCW). Every answer cites the exact RCW section it came from — if the law isn't in the database, it says "I don't know" instead of guessing.

**Live Demo:** https://chatbot-washinton-law-website.vercel.app

## Features

- Semantic search over Washington State law using vector embeddings
- Direct RCW citation lookup (e.g. "What does RCW 9A.36.041 say?")
- Anti-hallucination: answers only from retrieved law, never from model knowledge
- Conversation history saved per session
- Clean professional UI with clickable RCW citations linking to official source

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (React, TypeScript) |
| Backend | FastAPI (Python 3.11+) |
| Database | Supabase PostgreSQL + pgvector |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | OpenAI GPT-4o-mini |
| Data | Washington RCW Titles 1, 9, 9A (1,059 sections) |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes (chat, history, auth)
│   │   ├── core/         # Embeddings, LLM, retrieval, prompts
│   │   ├── db/           # Supabase client and SQL queries
│   │   └── models/       # Pydantic models
│   └── data_pipeline/    # Scraper, parser, loader, embedder
├── database/             # SQL schema, indexes, RLS policies
├── frontend/             # Next.js app
└── .env.example          # Environment variable template
```

## Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | https://chatbot-washinton-law-website.vercel.app |
| Backend | Render | https://chatbot-washinton-law-website.onrender.com |
| Database | Supabase | PostgreSQL + pgvector (hosted) |

### Deploy your own

**Backend (Render):**
- Connect your GitHub repo — Render auto-detects `render.yaml`
- Set environment variables in the Render dashboard (see list below)
- Use the **Supabase Connection Pooler URL** (port 6543) for `DATABASE_URL` — the direct connection URL is IPv6-only and won't work on most platforms
- Set `ALLOWED_ORIGINS` to your Vercel frontend URL

**Frontend (Vercel):**
- Set Root Directory to `frontend`
- Add `NEXT_PUBLIC_API_URL` = your Render backend URL
- Redeploy after setting env vars (the value is baked in at build time)

## Getting Started

### 1. Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project
- OpenAI API key

### 2. Clone and configure

```bash
git clone <your-repo-url>
cd chatbot_washinton_law_website-main
cp .env.example backend/.env
```

Fill in `backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres.your-project:password@aws-0-us-west-2.pooler.supabase.com:6543/postgres
OPENAI_API_KEY=sk-...
```

### 3. Set up the database

In Supabase SQL Editor, run in order:

```
database/01_schema.sql
database/02_indexes.sql
database/03_rls_policies.sql
```

Then remove the auth foreign key (not needed without auth):

```sql
ALTER TABLE conversations DROP CONSTRAINT conversations_user_id_fkey;
```

### 4. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Run the data pipeline

```bash
cd backend

# Scrape RCW from leg.wa.gov
python -m data_pipeline.run scrape --titles 1 9 9A

# Parse HTML into JSON
python -m data_pipeline.run parse --titles 1 9 9A

# Load into Supabase
python -m data_pipeline.run load --titles 1 9 9A

# Generate vector embeddings
python -m data_pipeline.run embed
```

### 6. Start the backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 7. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/query` | Ask a legal question |
| GET | `/api/history/{session_id}` | List conversations |
| GET | `/api/history/{session_id}/{conv_id}` | Load messages |

### Example request

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is assault in the fourth degree?"}'
```

## Test Questions

### Criminal Law (Title 9A)
- What is assault in the fourth degree?
- What is the difference between first and second degree murder in Washington?
- What counts as robbery in Washington State?
- What is the definition of burglary under Washington law?
- What does Washington law say about stalking?
- What is malicious mischief and what are the penalties?

### Weapons (Title 9)
- Can someone carry a concealed gun in Washington State?
- Who is prohibited from owning a firearm in Washington?
- What are the rules for purchasing a pistol in Washington State?
- What is the penalty for possessing an illegal weapon?

### Direct RCW Lookup
- What does RCW 9A.36.041 say?
- What does RCW 9.41.010 say?
- What does RCW 9A.56.200 say?

### Edge Cases (should say "I don't know")
- What is the penalty for jaywalking? *(not in covered titles)*
- What does Washington law say about income taxes? *(not covered)*
- What is the speed limit in Washington? *(not covered)*

## How It Works

1. User submits a question
2. The question is embedded using OpenAI text-embedding-3-small
3. pgvector finds the most similar law sections (cosine similarity)
4. If similarity is too low (score > 0.4), no results are returned → "I don't know"
5. Retrieved law sections are passed to GPT-4o-mini with a strict prompt
6. The model answers only from the retrieved text and cites the RCW sections used
7. The answer and conversation are saved to Supabase

## Environment Variables

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `DATABASE_URL` | PostgreSQL connection string |
| `OPENAI_API_KEY` | OpenAI API key |
| `EMBEDDING_PROVIDER` | `openai` or `huggingface` |
| `EMBEDDING_MODEL` | Default: `text-embedding-3-small` |
| `LLM_PROVIDER` | `openai` |
| `LLM_MODEL` | Default: `gpt-4o-mini` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend URLs |
