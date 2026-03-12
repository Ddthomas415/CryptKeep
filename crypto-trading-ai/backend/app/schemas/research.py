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
        response_asset = str(asset or "SOL").strip() or "SOL"
        asset_symbol = response_asset.upper()
        templates: dict[str, dict] = {
            "SOL": {
                "current_cause": "SOL is rising alongside increased spot volume and fresh ecosystem headlines.",
                "past_precedent": "Similar moves previously followed ecosystem upgrade narratives.",
                "future_catalyst": "A scheduled governance milestone may still matter.",
                "confidence": 0.78,
                "evidence": [
                    EvidenceItem(
                        id="ev_sol_1",
                        type="market",
                        source="coinbase",
                        timestamp="2026-03-11T12:55:00Z",
                        summary="SOL spot volume expanded over the last hour.",
                        relevance=0.92,
                    )
                ],
            },
            "BTC": {
                "current_cause": "BTC is firming as spot demand absorbs intraday pullbacks near range highs.",
                "past_precedent": "Comparable breakouts often held when liquidity improved into the U.S. session close.",
                "future_catalyst": "Macro prints later this week could determine whether continuation volume holds.",
                "confidence": 0.74,
                "evidence": [
                    EvidenceItem(
                        id="ev_btc_1",
                        type="market",
                        source="coinbase",
                        timestamp="2026-03-11T12:45:00Z",
                        summary="BTC held above intraday support while spot bid depth stayed firm.",
                        relevance=0.88,
                    )
                ],
            },
            "ETH": {
                "current_cause": "ETH is trading with steadier follow-through as upgrade narratives stay in focus.",
                "past_precedent": "Earlier pre-upgrade phases often rotated between compression and short expansion bursts.",
                "future_catalyst": "The next protocol milestone remains the clearest medium-term catalyst.",
                "confidence": 0.69,
                "evidence": [
                    EvidenceItem(
                        id="ev_eth_1",
                        type="news",
                        source="newsapi",
                        timestamp="2026-03-11T11:20:00Z",
                        summary="Upgrade commentary is supporting ETH interest without a full breakout.",
                        relevance=0.83,
                    )
                ],
            },
        }
        selected = templates.get(
            asset_symbol,
            {
                "current_cause": f"{asset_symbol} is moving with renewed market attention and higher watchlist activity.",
                "past_precedent": f"Past {asset_symbol} expansions often followed improving liquidity and fresh narrative flow.",
                "future_catalyst": f"The next catalyst for {asset_symbol} is whether follow-through volume confirms the move.",
                "confidence": 0.64,
                "evidence": [
                    EvidenceItem(
                        id=f"ev_{asset_symbol.lower()}_1",
                        type="market",
                        source="watchlist",
                        timestamp=None,
                        summary=f"{asset_symbol} is being actively monitored in the market watchlist.",
                        relevance=0.75,
                    )
                ],
            },
        )
        return cls(
            asset=response_asset,
            question=question,
            current_cause=str(selected["current_cause"]),
            past_precedent=str(selected["past_precedent"]),
            future_catalyst=str(selected["future_catalyst"]),
            confidence=float(selected["confidence"]),
            risk_note="Research only. Execution disabled.",
            execution_disabled=True,
            evidence=list(selected["evidence"]),
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
