from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    source: str
    title: str
    url: str | None = None
    timeline: str
    confidence: float
    published_at: datetime | None = None
    snippet: str | None = None


class DocumentSearchRequest(BaseModel):
    query: str
    asset: str
    timeline: list[str] = Field(default_factory=lambda: ["past", "present", "future"])
    limit: int = 10


class DocumentSearchResponse(BaseModel):
    results: list[DocumentOut]
