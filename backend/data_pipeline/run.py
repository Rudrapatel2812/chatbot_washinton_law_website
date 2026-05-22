from __future__ import annotations

import argparse
import asyncio
import logging

from data_pipeline.config import DEFAULT_TITLES
from data_pipeline.parser import parse_title
from data_pipeline.scraper import RcwScraper


logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["scrape", "parse", "load", "embed"])
    parser.add_argument("--titles", nargs="+", default=list(DEFAULT_TITLES))
    parser.add_argument("--jurisdiction-code", default="WA")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    if args.stage == "scrape":
        scraper = RcwScraper(requests_per_second=5)
        await scraper.scrape_titles(args.titles)
        return

    if args.stage == "parse":
        for title in args.titles:
            written = parse_title(title, args.jurisdiction_code)
            logger.info("title_parsed title=%s count=%s", title, len(written))
        return

    from app.config import get_settings
    from app.core.provider_factory import build_embedding_provider
    from app.db.supabase_client import Database
    from data_pipeline.loader import load_title

    settings = get_settings()
    database = Database(settings)

    if args.stage == "embed":
        from data_pipeline.embedder import embed_all
        embedding_provider = build_embedding_provider(settings)
        count = await embed_all(database, embedding_provider)
        logger.info("embed_complete total=%s", count)
        await database.close()
        return

    for title in args.titles:
        loaded = await load_title(database, title)
        logger.info("title_loaded title=%s count=%s", title, loaded)
    await database.close()


if __name__ == "__main__":
    asyncio.run(main())
