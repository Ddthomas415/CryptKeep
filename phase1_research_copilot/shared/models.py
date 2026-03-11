from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

TimelineTag = Literal["past", "present", "future"]


class AuditEvent(BaseModel):
    service: str
    action: str
    status: str = "ok"
    correlation_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class NormalizedDocument(BaseModel):
    source_type: Literal["news", "archive", "manual"] = "news"
    source: str
    url: str
    title: str
    content_text: str
    timeline_tag: TimelineTag = "present"
    asset_tags: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    content_hash: str
    published_at: datetime | None = None
    fetched_at: datetime
    raw_html: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrieveRequest(BaseModel):
    asset: str
    question: str = ""
    lookback_minutes: int = 60
    limit: int = 5


class ExplainRequest(BaseModel):
    asset: str
    question: str
    lookback_minutes: int = 60
