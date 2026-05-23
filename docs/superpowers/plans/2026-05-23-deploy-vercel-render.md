# Deploy to Vercel + Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix pre-deployment bugs, verify the app works locally end-to-end, then deploy the FastAPI backend to Render and the Next.js frontend to Vercel.

**Architecture:** FastAPI backend on Render (free tier, Python 3.11) connects to existing Supabase PostgreSQL and OpenAI. Next.js frontend on Vercel (free tier) talks to the backend via `NEXT_PUBLIC_API_URL` env var. CORS origins on the backend are configurable via env var so the Vercel domain is accepted.

**Tech Stack:** FastAPI + uvicorn + asyncpg (backend), Next.js 16 + React 19 + Tailwind (frontend), Supabase PostgreSQL + pgvector (database, already hosted), OpenAI API (embeddings + LLM).

---

## Pre-Deployment Bug Inventory

Before deploying, these bugs will cause failures:

| # | File | Problem |
|---|------|---------|
| 1 | `backend/requirements.txt` | `structlog` is imported in `main.py` but not listed — Render will fail to import |
| 2 | `backend/app/main.py` | CORS only allows `localhost:3000` — Vercel frontend requests will be blocked |
| 3 | `backend/app/config.py` | No `allowed_origins` setting — CORS can't be configured without a code change |
| 4 | (missing) | No `render.yaml` — Render won't know how to build/start the service |
| 5 | (missing) | No `runtime.txt` — Render will pick an old Python version |

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/requirements.txt` | Modify | Add `structlog` |
| `backend/app/config.py` | Modify | Add `allowed_origins` and `port` settings |
| `backend/app/main.py` | Modify | Read CORS origins from settings instead of hardcoding |
| `backend/runtime.txt` | Create | Pin Python 3.11 for Render |
| `render.yaml` | Create | Render service definition (build + start command + env vars) |

---

## Task 1: Fix `structlog` missing from requirements

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add structlog to requirements**

Open `backend/requirements.txt` and add `structlog==24.4.0` after the uvicorn line:

```text
asyncpg==0.29.0
beautifulsoup4==4.12.3
fastapi==0.115.6
httpx==0.27.2
openai==1.58.1
pydantic==2.10.4
pydantic-settings==2.7.0
python-dotenv==1.0.1
structlog==24.4.0
tenacity==9.0.0
uvicorn[standard]==0.34.0

# Test dependencies
pytest==8.3.4
pytest-asyncio==0.25.0
```

- [ ] **Step 2: Verify the fix imports correctly**

Run from the `backend/` directory:
```bash
cd backend
pip install structlog==24.4.0
python -c "import structlog; print('ok')"
```
Expected output: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "fix: add missing structlog dependency"
```

---

## Task 2: Make CORS origins configurable

The backend currently hardcodes `http://localhost:3000` in CORS. When deployed, requests from `https://your-app.vercel.app` will be rejected with a CORS error.

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add `allowed_origins` to Settings**

Edit `backend/app/config.py`. Replace the current `Settings` class body with:

```python
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Washington Legal Chatbot"
    app_env: str = "development"
    log_level: str = "INFO"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None

    # Comma-separated list of allowed CORS origins
    # Default covers local dev. In production, set to your Vercel URL.
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    rcw_base_url: str = "https://app.leg.wa.gov/rcw/"
    scraper_max_requests_per_second: int = Field(default=5, ge=1, le=5)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: Update CORS in main.py to use settings**

Edit `backend/app/main.py`. Replace the full file content with:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.api import auth, chat, history
from app.config import get_settings


settings = get_settings()
logger = structlog.get_logger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(history.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    logger.info("health_check", app_env=settings.app_env)
    return {"status": "ok", "environment": settings.app_env}
```

- [ ] **Step 3: Verify CORS config parses correctly**

Run from `backend/`:
```bash
cd backend
python -c "from app.config import get_settings; s = get_settings(); print(s.get_allowed_origins())"
```
Expected output: `['http://localhost:3000', 'http://127.0.0.1:3000']`

- [ ] **Step 4: Commit**

```bash
git add backend/app/config.py backend/app/main.py
git commit -m "fix: make CORS origins configurable via ALLOWED_ORIGINS env var"
```

---

## Task 3: Add Python version file for Render

**Files:**
- Create: `backend/runtime.txt`

- [ ] **Step 1: Create runtime.txt**

Create the file `backend/runtime.txt` with content:

```
python-3.11.9
```

This tells Render to use Python 3.11, matching the project requirement.

- [ ] **Step 2: Commit**

```bash
git add backend/runtime.txt
git commit -m "chore: pin Python 3.11 for Render deployment"
```

---

## Task 4: Add render.yaml

**Files:**
- Create: `render.yaml` (at repo root)

- [ ] **Step 1: Create render.yaml**

Create `render.yaml` at the project root with this content:

```yaml
services:
  - type: web
    name: wa-legal-chatbot-api
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: APP_ENV
        value: production
      - key: LOG_LEVEL
        value: INFO
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: EMBEDDING_PROVIDER
        value: openai
      - key: EMBEDDING_MODEL
        value: text-embedding-3-small
      - key: LLM_PROVIDER
        value: openai
      - key: LLM_MODEL
        value: gpt-4o-mini
      - key: ALLOWED_ORIGINS
        sync: false
    healthCheckPath: /health
```

`sync: false` means Render will prompt you to set the value in the dashboard — it will not be committed to the repo. This is the secure approach.

- [ ] **Step 2: Commit**

```bash
git add render.yaml
git commit -m "chore: add render.yaml for Render deployment"
```

---

## Task 5: Verify backend runs locally

Run the backend locally and hit its health endpoint to confirm everything is wired up before deploying.

**Prerequisites:** You must have a valid `backend/.env` with real values for `DATABASE_URL`, `OPENAI_API_KEY`, and `SUPABASE_URL`.

- [ ] **Step 1: Install dependencies**

```bash
cd backend
pip install -r requirements.txt
```
Expected: all packages installed, no errors.

- [ ] **Step 2: Start the server**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Expected: output like `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 3: Hit the health endpoint**

In a separate terminal:
```bash
curl http://localhost:8000/health
```
Expected output:
```json
{"status":"ok","environment":"development"}
```

- [ ] **Step 4: Hit the auth status endpoint**

```bash
curl http://localhost:8000/api/auth/status
```
Expected:
```json
{"status":"supabase-auth-planned"}
```

- [ ] **Step 5: Test a real query (optional but recommended)**

```bash
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is assault in the fourth degree?","session_id":"test-local-123"}' | python -m json.tool
```
Expected: JSON with `answer` and `citations` keys. If the database has no embeddings yet, you may get an "I don't know" style answer — that is correct behavior.

- [ ] **Step 6: Stop the server**

Press `Ctrl+C` in the uvicorn terminal.

---

## Task 6: Verify frontend builds and connects to backend

- [ ] **Step 1: Install frontend dependencies**

```bash
cd frontend
npm install
```
Expected: `added N packages` with no errors.

- [ ] **Step 2: Create a local env file**

Create `frontend/.env.local` (it's gitignored, so this is safe):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 3: Start the backend** (if not already running)

In a separate terminal:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 4: Start the frontend**

```bash
cd frontend
npm run dev
```
Expected: `Local: http://localhost:3000`

- [ ] **Step 5: Open the app in a browser**

Navigate to `http://localhost:3000`.

Verify:
- The chat UI loads with the sidebar and disclaimer banner
- The "WA Legal" logo and three example questions appear
- Click one of the example questions — it should populate the input box
- Press Enter or click Send — you should see a response (or a graceful error if the DB has no data)
- No CORS errors in the browser DevTools console

- [ ] **Step 6: Run the production build**

```bash
cd frontend
npm run build
```
Expected: `Route (app) ✓ Compiled successfully`. No TypeScript errors.

---

## Task 7: Deploy backend to Render

- [ ] **Step 1: Push all changes to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Create a new Render Web Service**

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repo (`chatbot_washinton_law_website-main`)
3. Render will detect `render.yaml` and pre-fill the settings

If Render doesn't auto-detect render.yaml, configure manually:
- **Name:** `wa-legal-chatbot-api`
- **Root Directory:** `backend`
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Free

- [ ] **Step 3: Set environment variables in Render dashboard**

In Render → Your Service → Environment, add these key/value pairs from your `backend/.env`:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | your Supabase project URL |
| `SUPABASE_ANON_KEY` | your anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | your service role key |
| `DATABASE_URL` | your full postgres connection string |
| `OPENAI_API_KEY` | your OpenAI key |
| `APP_ENV` | `production` |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` (fill in after Vercel deploy) |

**Note:** Leave `ALLOWED_ORIGINS` as `http://localhost:3000` temporarily. You will update it after getting the Vercel URL.

- [ ] **Step 4: Trigger a deploy and wait**

Click "Deploy". Watch the build logs. Expected final lines:
```
==> Starting service with 'uvicorn app.main:app --host 0.0.0.0 --port $PORT'
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

- [ ] **Step 5: Verify the deployed backend**

Your Render service URL will be `https://wa-legal-chatbot-api.onrender.com` (or similar).

```bash
curl https://wa-legal-chatbot-api.onrender.com/health
```
Expected:
```json
{"status":"ok","environment":"production"}
```

**Note:** The free tier sleeps after 15 minutes of inactivity. The first request after sleep takes ~30 seconds. This is expected.

---

## Task 8: Deploy frontend to Vercel

- [ ] **Step 1: Go to vercel.com → New Project**

1. Import your GitHub repo
2. In **Configure Project**, set:
   - **Framework Preset:** Next.js (auto-detected)
   - **Root Directory:** `frontend`
3. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL` = `https://wa-legal-chatbot-api.onrender.com` (your Render URL from Task 7)
4. Click **Deploy**

- [ ] **Step 2: Wait for build to complete**

Expected: Vercel build logs end with `✓ Build completed`. You get a URL like `https://wa-legal-chatbot-api-xyz.vercel.app`.

- [ ] **Step 3: Update ALLOWED_ORIGINS on Render**

Go back to Render → Your Service → Environment → edit `ALLOWED_ORIGINS`:
```
https://wa-legal-chatbot-api-xyz.vercel.app
```
Click "Save Changes" — Render will redeploy automatically.

---

## Task 9: Verify end-to-end in production

- [ ] **Step 1: Open the Vercel URL in your browser**

Navigate to your Vercel deployment URL.

Verify:
- Chat UI loads correctly
- No CORS errors in browser DevTools → Network tab
- The disclaimer banner is visible

- [ ] **Step 2: Send a test question**

Type: `What is assault in the fourth degree?`

Expected:
- A response appears (even if it's "I don't know" due to empty DB — that means the pipeline is working)
- The conversation appears in the sidebar
- No network errors in DevTools

- [ ] **Step 3: Test conversation history**

1. Send a second message in the same conversation
2. Start a new conversation (click "New Conversation")
3. Click back to the first — messages should reload

- [ ] **Step 4: Verify CORS with a curl test**

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Origin: https://your-app.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  https://wa-legal-chatbot-api.onrender.com/api/query
```
Expected: `200` (not `403`)

---

## Environment Variable Summary

### Render (backend)

| Variable | Example Value | Source |
|----------|--------------|--------|
| `APP_ENV` | `production` | Hardcode |
| `LOG_LEVEL` | `INFO` | Hardcode |
| `SUPABASE_URL` | `https://xxxx.supabase.co` | Your Supabase project |
| `SUPABASE_ANON_KEY` | `eyJ...` | Supabase → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` | Supabase → Settings → API |
| `DATABASE_URL` | `postgresql://postgres:pw@db.xxxx.supabase.co:5432/postgres` | Supabase → Settings → Database |
| `OPENAI_API_KEY` | `sk-...` | OpenAI platform |
| `EMBEDDING_PROVIDER` | `openai` | Hardcode |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Hardcode |
| `LLM_PROVIDER` | `openai` | Hardcode |
| `LLM_MODEL` | `gpt-4o-mini` | Hardcode |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` | Set after Vercel deploys |

### Vercel (frontend)

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://wa-legal-chatbot-api.onrender.com` |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Render build fails: `ModuleNotFoundError: No module named 'structlog'` | Old requirements.txt cached | Task 1 not committed; push again |
| CORS error in browser console | `ALLOWED_ORIGINS` not updated with Vercel URL | Task 8 Step 3 |
| Render health returns 503 | `DATABASE_URL` not set or wrong | Check Render env vars |
| Vercel build fails: TypeScript error | Run `npm run build` locally first | Task 6 Step 6 |
| Render sleeps, first request times out | Free tier behavior | Normal; Render Starter ($7/mo) eliminates this |
| `uvicorn: command not found` on Render | Wrong start command | Ensure `uvicorn[standard]` is in requirements.txt |
