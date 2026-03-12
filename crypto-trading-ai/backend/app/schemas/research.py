from pydantic import BaseModel


class ResearchFilters(BaseModel):
    exchange: str | None = None
    source_types: list[str] | None = None
    timelines: list[str] | None = None
    time_range: str | None = None
    confidence_min: float | None = None
    include_archives: bool | None = None
    include_onchain: bool | None = None
    include_social: bool | None = None


class ExplainRequest(BaseModel):
    question: str
    asset: str
    filters: ResearchFilters | dict | None = None


class EvidenceItem(BaseModel):
    id: str
    type: str
    source: str
    timestamp: str | None = None
    summary: str
    relevance: float | None = None


class ExplainResponse(BaseModel):
    asset: str
    question: str
    current_cause: str
    past_precedent: str
    future_catalyst: str
    confidence: float
    risk_note: str | None = None
    execution_disabled: bool
    evidence: list[EvidenceItem]

    @classmethod
    def example(cls, asset: str = "SOL", question: str = "Why is SOL moving?") -> dict:
        return cls(
            asset=asset,
            question=question,
            current_cause="SOL is rising alongside increased spot volume and fresh ecosystem headlines.",
            past_precedent="Similar moves previously followed ecosystem upgrade narratives.",
            future_catalyst="A scheduled governance milestone may still matter.",
            confidence=0.78,
            risk_note="Research only. Execution disabled.",
            execution_disabled=True,
            evidence=[
                EvidenceItem(
                    id="ev1",
                    type="market",
                    source="coinbase",
                    timestamp="2026-03-11T12:55:00Z",
                    summary="Volume expansion over the last hour.",
                    relevance=0.92,
                )
            ],
        ).model_dump()


class ResearchSearchItem(BaseModel):
    id: str
    type: str
    source: str
    title: str
    summary: str
    timeline: str
    timestamp: str
    confidence: float
    relevance: float


class SearchRequest(BaseModel):
    query: str
    asset: str | None = None
    filters: ResearchFilters | dict | None = None
    page: int = 1
    page_size: int = 20


class ResearchSearchResponse(BaseModel):
    items: list[ResearchSearchItem]
