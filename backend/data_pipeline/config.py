from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html"
PARSED_JSON_DIR = DATA_DIR / "parsed_json"


DEFAULT_TITLES = ("1", "9", "9A", "15")


class PipelineTitle(BaseModel):
    title_number: str
    url: str


class RawHtmlRecord(BaseModel):
    title_number: str
    citation: str
    source_url: str
    raw_html_path: str


class RawHtmlManifest(BaseModel):
    title_number: str
    records: list[RawHtmlRecord] = Field(default_factory=list)


def title_url(title_number: str) -> str:
    return f"https://app.leg.wa.gov/rcw/default.aspx?Cite={title_number}"


def title_raw_dir(title_number: str) -> Path:
    return RAW_HTML_DIR / f"title_{title_number}"


def title_parsed_dir(title_number: str) -> Path:
    return PARSED_JSON_DIR / f"title_{title_number}"


def citation_to_filename(citation: str) -> str:
    return citation.replace(".", "_").replace("/", "_") + ".html"
