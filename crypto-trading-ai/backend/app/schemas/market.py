from __future__ import annotations

from pydantic import BaseModel


class MarketSnapshot(BaseModel):
    asset: str
    exchange: str
    last_price: float
    bid: float | None = None
    ask: float | None = None
    spread: float | None = None
    volume_24h: float | None = None
    timestamp: str | None = None


class MarketCandle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class MarketCandlesResponse(BaseModel):
    asset: str
    exchange: str
    interval: str
    candles: list[MarketCandle]
