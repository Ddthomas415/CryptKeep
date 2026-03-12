from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    id: str
    asset: str
    side: str
    strategy: str
    confidence: float = Field(ge=0, le=1)
    entry_zone: str | None = None
    stop: str | None = None
    target_logic: str | None = None
    risk_size_pct: float | None = None
    mode_compatibility: list[str]
    approval_required: bool
    status: str
    execution_disabled: bool


class RecommendationList(BaseModel):
    items: list[RecommendationItem]
