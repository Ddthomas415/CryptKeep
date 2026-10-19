from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

TimelineTag = Literal["past", "present", "future"]
FreshnessStatus = Literal["fresh", "aging", "stale", "missing"]
MetadataStatus = Literal["ok", "warn", "critical", "unknown"]
ConfidenceLabel = Literal["High", "Medium", "Low", "Unknown"]


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


class AnswerMetadata(BaseModel):
    as_of: str
    source_type: str = "fallback"
    source_family: str = "fallback"
    source_ids: list[str] = Field(default_factory=list)
    freshness_status: FreshnessStatus = "missing"
    age_seconds: int | None = None
    confidence_label: ConfidenceLabel = "Unknown"
    caveat: str | None = None
    partial_provenance: bool = True
    missing_provenance_reason: str | None = None
    source_name: str | None = None
    source_names: list[str] = Field(default_factory=list)
    data_timestamp: str | None = None
    metadata_status: MetadataStatus = "unknown"
