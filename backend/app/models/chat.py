from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.law import RetrievedLaw


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    session_id: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    conversation_id: Optional[str] = None
    jurisdiction_code: str = "WA"


class Citation(BaseModel):
    citation: str
    source_url: str
    excerpt: str


class Answer(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_laws: list[RetrievedLaw]
    confidence: str
    conversation_id: Optional[str] = None


class Conversation(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime


class Message(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime
