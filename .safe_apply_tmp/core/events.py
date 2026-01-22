from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Venue(str, Enum):
    BINANCE = "binance"
    COINBASE = "coinbase"
    GATEIO = "gateio"


class Channel(str, Enum):
    TRADES = "trades"
    BOOK_L2 = "book_l2"
    CANDLES = "candles"
    FUNDING = "funding"
    OPEN_INTEREST = "open_interest"
    SIGNALS = "signals"


class EventBase(BaseModel):
    """Canonical event base type.

    Rules:
    - ts MUST be timezone-aware UTC.
    - symbol uses exchange-native symbol string for now (normalize later in Phase 2).
    """
    model_config = ConfigDict(extra="forbid")

    event_type: str
    venue: str
    symbol: str
    ts: datetime = Field(default_factory=utc_now)

    @field_validator("ts")
    @classmethod
    def ts_must_be_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("ts must be timezone-aware (UTC recommended)")
        return v


class TradeEvent(EventBase):
    event_type: Literal["trade"] = "trade"
    price: float
    size: float
    side: Literal["buy", "sell"]  # aggressor side if known
    trade_id: Optional[str] = None


class BookLevel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    price: float
    size: float


class BookEvent(EventBase):
    """L2 order book snapshot or delta."""
    event_type: Literal["book_l2"] = "book_l2"
    kind: Literal["snapshot", "delta"] = "snapshot"
    bids: List[BookLevel] = Field(default_factory=list)
    asks: List[BookLevel] = Field(default_factory=list)
    sequence: Optional[int] = None


class CandleEvent(EventBase):
    event_type: Literal["candle"] = "candle"
    timeframe: str  # e.g. "1m", "5m", "1h"
    o: float
    h: float
    l: float
    c: float
    v: float


class FundingEvent(EventBase):
    event_type: Literal["funding"] = "funding"
    rate: float
    next_funding_ts: Optional[datetime] = None


class OpenInterestEvent(EventBase):
    event_type: Literal["open_interest"] = "open_interest"
    open_interest: float
    notional: Optional[float] = None


class SignalEvent(EventBase):
    """External/internal signal (e.g., TradingView webhook or in-house model)."""
    event_type: Literal["signal"] = "signal"
    source: str  # e.g. "tradingview", "leader_X", "model_v12"
    direction: Literal["long", "short", "flat"]
    confidence: float = Field(ge=0.0, le=1.0)
    ttl_sec: int = Field(default=60, ge=1, le=86_400)
    payload: Dict[str, Any] = Field(default_factory=dict)
