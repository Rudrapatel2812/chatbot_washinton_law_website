from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from app.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if not self._settings.database_url:
            raise RuntimeError("DATABASE_URL is not configured.")
        self._pool = await asyncpg.create_pool(str(self._settings.database_url), min_size=1, max_size=10)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        if self._pool is None:
            await self.connect()
        if self._pool is None:
            raise RuntimeError("Database pool failed to initialize.")
        async with self._pool.acquire() as connection:
            yield connection
