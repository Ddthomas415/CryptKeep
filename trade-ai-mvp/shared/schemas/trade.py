from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TradeProposalRequest(BaseModel):
    asset: str
    question: str | None = None
    max_notional_usd: float = Field(default=250.0, gt=0)


class TradeProposalResponse(BaseModel):
    asset: str
    question: str
    side: Literal["buy", "sell", "hold"] = "hold"
    order_type: Literal["market"] = "market"
    suggested_quantity: float = 0.0
    estimated_price: float | None = None
    estimated_notional_usd: float = 0.0
    rationale: str
    confidence: float
    risk: dict[str, Any] = Field(default_factory=dict)
    execution_disabled: bool = True
    requires_user_approval: bool = True
    paper_submit_path: str = "/paper/orders"
