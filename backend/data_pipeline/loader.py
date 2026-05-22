import json
from pathlib import Path

from app.db.queries import insert_law
from app.db.supabase_client import Database
from app.models.law import ParsedLawDocument
from data_pipeline.config import title_parsed_dir


async def load_title(database: Database, title_number: str) -> int:
    parsed_dir = title_parsed_dir(title_number)
    paths = sorted(parsed_dir.glob("*.json"))
    loaded = 0

    async with database.acquire() as connection:
        async with connection.transaction():
            for path in paths:
                payload = json.loads(path.read_text(encoding="utf-8"))
                document = ParsedLawDocument.model_validate(payload)
                await insert_law(connection, document.law)
                loaded += 1

    return loaded
