from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

import app.dependencies as deps
from app.api import auth, chat, history
from app.config import get_settings
from app.core.provider_factory import build_embedding_provider, build_llm_provider
from app.db.supabase_client import Database
from app.limiter import limiter

settings = get_settings()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    deps._database = Database(settings)
    await deps._database.connect()
    deps._embedding_provider = build_embedding_provider(settings)
    deps._llm_provider = build_llm_provider(settings)
    logger.info("app_startup", db="connected", providers="initialized")
    yield
    await deps._database.close()
    logger.info("app_shutdown")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)

app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(history.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    logger.info("health_check", app_env=settings.app_env)
    return {"status": "ok", "environment": settings.app_env}
