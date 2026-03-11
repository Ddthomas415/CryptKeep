from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    asset: str
    question: str


class EvidenceItem(BaseModel):
    type: str
    source: str
    timestamp: datetime | None = None
    title: str | None = None


class ExplainResponse(BaseModel):
    asset: str
    question: str
    current_cause: str
    past_precedent: str
    future_catalyst: str
    confidence: float
    evidence: list[EvidenceItem] = Field(default_factory=list)
    paper_positions: list[dict[str, Any]] = Field(default_factory=list)
    recent_paper_fills: list[dict[str, Any]] = Field(default_factory=list)
    paper_risk_state: dict[str, Any] = Field(default_factory=dict)
    execution_disabled: bool = True
