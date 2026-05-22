from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from app.models.law import Law, LawStatus, ParsedLawDocument
from data_pipeline.config import RawHtmlManifest, title_parsed_dir, title_raw_dir


PARSER_VERSION = "rcw_parser_v1"


def parse_title(title_number: str, jurisdiction_code: str = "WA") -> list[Path]:
    raw_dir = title_raw_dir(title_number)
    manifest_path = raw_dir / "manifest.json"
    manifest = RawHtmlManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    output_dir = title_parsed_dir(title_number)
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for record in manifest.records:
        if not record.citation.upper().startswith(title_number.upper() + "."):
            continue
        html = Path(record.raw_html_path).read_text(encoding="utf-8")
        document = parse_section_html(
            html=html,
            jurisdiction_code=jurisdiction_code,
            title_number=record.title_number,
            citation=record.citation,
            source_url=record.source_url,
            raw_html_path=record.raw_html_path,
        )
        output_path = output_dir / f"{record.citation.replace('.', '_')}.json"
        output_path.write_text(json.dumps(document.model_dump(), indent=2), encoding="utf-8")
        written.append(output_path)
    return written


def parse_section_html(
    html: str,
    jurisdiction_code: str,
    title_number: str,
    citation: str,
    source_url: str,
    raw_html_path: str,
) -> ParsedLawDocument:
    soup = BeautifulSoup(html, "html.parser")
    parsed_citation = _extract_citation(soup) or citation
    heading = _extract_heading(soup)
    body_text, history, notes = _extract_section_parts(soup)
    text = body_text or _extract_body_text(soup)
    status = _detect_status(text)
    chapter_number = ".".join(parsed_citation.split(".")[:2])

    law = Law(
        jurisdiction_code=jurisdiction_code,
        citation=parsed_citation.upper(),
        title_number=title_number.upper(),
        chapter_number=chapter_number.upper(),
        section_number=parsed_citation.upper(),
        heading=heading,
        text=text,
        history=history,
        notes=notes,
        source_url=source_url,
        status=status,
    )
    return ParsedLawDocument(law=law, raw_html_path=raw_html_path, parser_version=PARSER_VERSION)


def _extract_citation(soup: BeautifulSoup) -> str | None:
    title = soup.select_one(".title-block h1")
    if not title:
        title = soup.find("h1")
    if not title:
        return None
    match = re.search(r"RCW\s+([0-9A-Z.]+)", title.get_text(" ", strip=True), re.IGNORECASE)
    return match.group(1).upper() if match else None


def _extract_heading(soup: BeautifulSoup) -> str | None:
    caption = soup.select_one(".title-block h2")
    if caption:
        text = _clean_text(caption.get_text(" ", strip=True))
        if text:
            return text

    for heading in soup.find_all(["h3", "h4"]):
        cleaned = _clean_text(heading.get_text(" ", strip=True))
        cleaned = re.sub(r"^RCW\s+[0-9A-Z.]+\s*", "", cleaned, flags=re.IGNORECASE).strip()
        if cleaned and not cleaned.lower().startswith(("pdf", "notes:")):
            return cleaned
    return None


def _extract_section_parts(soup: BeautifulSoup) -> tuple[str, str | None, str | None]:
    wrapper = soup.select_one("#contentWrapper.section-page") or soup.find(id="contentWrapper")
    if not wrapper:
        return "", None, None

    paragraphs: list[str] = []
    history_parts: list[str] = []
    note_parts: list[str] = []
    in_notes = False

    for child in wrapper.find_all(recursive=False):
        text = _clean_text(child.get_text(" ", strip=True))
        if not text:
            continue

        if text.lower().startswith("notes:"):
            in_notes = True
            remaining = text[len("Notes:") :].strip()
            if remaining:
                note_parts.append(remaining)
            continue

        if in_notes:
            note_parts.append(text)
            continue

        if text.startswith("[") and text.endswith("]"):
            history_parts.append(text)
            continue

        paragraphs.append(text)

    return (
        "\n\n".join(paragraphs),
        "\n".join(history_parts) or None,
        "\n".join(note_parts) or None,
    )


def _extract_body_text(soup: BeautifulSoup) -> str:
    content = soup.find(id="contentstart") or soup.find("body") or soup
    for element in content.select("script, style, nav, footer, #wsl-header, .breadcrumb-line"):
        element.decompose()
    return _clean_text(content.get_text(" ", strip=True))


def _detect_status(text: str) -> LawStatus:
    lowered = text.lower()
    if "[repealed" in lowered or "repealed." in lowered:
        return LawStatus.repealed
    if "[reserved" in lowered:
        return LawStatus.reserved
    if "recodified" in lowered:
        return LawStatus.recodified
    return LawStatus.active


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
