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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
