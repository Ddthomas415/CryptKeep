from typing import Literal

from pydantic import BaseModel, Field

RecommendationSide = Literal["buy", "sell"]
RecommendationStatus = Literal["draft", "pending_review", "approved", "rejected", "expired"]
ModeCompatibility = Literal["research_only", "paper", "live_approval", "live_auto"]


class RecommendationItem(BaseModel):
    id: str
    asset: str
    side: RecommendationSide
    strategy: str
    confidence: float = Field(ge=0, le=1)
    entry_zone: str | None = None
    stop: str | None = None
    target_logic: str | None = None
    risk_size_pct: float | None = None
    mode_compatibility: list[ModeCompatibility]
    approval_required: bool
    status: RecommendationStatus
    execution_disabled: bool


class RecommendationList(BaseModel):
    items: list[RecommendationItem]
