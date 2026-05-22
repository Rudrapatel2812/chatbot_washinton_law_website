from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from data_pipeline.config import (
    RawHtmlManifest,
    RawHtmlRecord,
    citation_to_filename,
    title_raw_dir,
    title_url,
)


logger = logging.getLogger(__name__)
SECTION_LINK_RE = re.compile(r"cite=([0-9A-Z]+\.[0-9]+\.[0-9]+)", re.IGNORECASE)
CHAPTER_LINK_RE = re.compile(r"cite=([0-9A-Z]+\.[0-9]+)$", re.IGNORECASE)


class AsyncRateLimiter:
    def __init__(self, requests_per_second: int) -> None:
        self._min_interval = 1 / requests_per_second
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def wait(self) -> None:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request_at
            sleep_for = self._min_interval - elapsed
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
            self._last_request_at = time.monotonic()


class RcwScraper:
    def __init__(self, requests_per_second: int = 5) -> None:
        self._limiter = AsyncRateLimiter(requests_per_second)

    async def scrape_titles(self, titles: list[str]) -> None:
        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "WashingtonLegalChatbot/0.1"},
        ) as client:
            for title_number in titles:
                await self.scrape_title(client, title_number)

    async def scrape_title(self, client: httpx.AsyncClient, title_number: str) -> None:
        output_dir = title_raw_dir(title_number)
        output_dir.mkdir(parents=True, exist_ok=True)

        chapters = await self._extract_chapter_urls(client, title_number)
        records: list[RawHtmlRecord] = []
        for chapter_url in chapters:
            section_urls = await self._extract_section_urls(client, chapter_url)
            for citation, section_url in section_urls.items():
                output_path = output_dir / citation_to_filename(citation)
                if output_path.exists():
                    logger.info("raw_html_exists citation=%s path=%s", citation, output_path)
                else:
                    html = await self._fetch_text(client, section_url)
                    output_path.write_text(html, encoding="utf-8")
                    logger.info("raw_html_saved citation=%s path=%s", citation, output_path)
                records.append(
                    RawHtmlRecord(
                        title_number=title_number,
                        citation=citation,
                        source_url=section_url,
                        raw_html_path=str(output_path),
                    )
                )

        manifest = RawHtmlManifest(title_number=title_number, records=records)
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest.model_dump(), indent=2),
            encoding="utf-8",
        )

    async def _extract_chapter_urls(self, client: httpx.AsyncClient, title_number: str) -> list[str]:
        html = await self._fetch_text(client, title_url(title_number))
        soup = BeautifulSoup(html, "html.parser")
        urls: set[str] = set()
        for link in soup.find_all("a", href=True):
            href = str(link["href"])
            match = CHAPTER_LINK_RE.search(href)
            if match and match.group(1).upper().startswith(title_number.upper() + "."):
                urls.add(_absolute_rcw_url(match.group(1)))
        logger.info("chapters_found title=%s count=%s", title_number, len(urls))
        return sorted(urls)

    async def _extract_section_urls(self, client: httpx.AsyncClient, chapter_url: str) -> dict[str, str]:
        html = await self._fetch_text(client, chapter_url)
        soup = BeautifulSoup(html, "html.parser")
        urls: dict[str, str] = {}
        chapter_match = re.search(r"cite=([0-9A-Z]+\.[0-9]+)", chapter_url, re.IGNORECASE)
        if not chapter_match:
            logger.warning("chapter_citation_not_found chapter_url=%s", chapter_url)
            return urls
        chapter_citation = chapter_match.group(1).upper()
        for link in soup.find_all("a", href=True):
            href = str(link["href"])
            match = SECTION_LINK_RE.search(href)
            if match and match.group(1).upper().startswith(chapter_citation + "."):
                citation = match.group(1).upper()
                urls[citation] = _absolute_rcw_url(citation)
        logger.info("sections_found chapter_url=%s count=%s", chapter_url, len(urls))
        return urls

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _fetch_text(self, client: httpx.AsyncClient, url: str) -> str:
        await self._limiter.wait()
        await asyncio.sleep(random.uniform(0.5, 1.5))
        response = await client.get(url)
        if response.status_code in {403, 404}:
            logger.warning("non_retryable_response url=%s status_code=%s", url, response.status_code)
            response.raise_for_status()
        if response.status_code == 429 or response.status_code >= 500:
            logger.warning("retryable_response url=%s status_code=%s", url, response.status_code)
            response.raise_for_status()
        return response.text


def _absolute_rcw_url(citation: str) -> str:
    return f"https://app.leg.wa.gov/RCW/default.aspx?cite={citation}"
