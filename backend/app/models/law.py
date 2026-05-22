from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LawStatus(str, Enum):
    active = "active"
    repealed = "repealed"
    reserved = "reserved"
    recodified = "recodified"
    unknown = "unknown"


class Jurisdiction(BaseModel):
    id: Optional[str] = None
    code: str
    name: str


class Law(BaseModel):
    id: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    jurisdiction_code: str = "WA"
    citation: str
    title_number: str
    chapter_number: str
    section_number: str
    heading: Optional[str] = None
    text: str
    history: Optional[str] = None
    notes: Optional[str] = None
    source_url: str
    status: LawStatus = LawStatus.active


class RetrievedLaw(BaseModel):
    law: Law
    score: Optional[float] = None
    retrieval_method: str


class ParsedLawDocument(BaseModel):
    law: Law
    raw_html_path: str
    parser_version: str = "rcw_parser_v1"


class LawEmbedding(BaseModel):
    law_id: str
    provider: str
    model: str
    dimensions: int
    embedding: list[float] = Field(min_length=1)
