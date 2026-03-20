from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class MarketSnapshotResponse(BaseModel):
    symbol: str
    exchange: str
    last_price: str
    bid: str
    ask: str
    spread: str
    timestamp: datetime
