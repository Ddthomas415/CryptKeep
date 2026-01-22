from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

@dataclass
class MarketContext:
    venue: str
    symbol: str
    timeframe: str
    ohlcv: list  # [[ts, o, h, l, c, v], ...]
    last_price: float

@dataclass
class PositionContext:
    base_amt: float
    avg_price: float
    cash_quote: float
    quote: str

@dataclass
class Signal:
    name: str
    action: str  # "buy" | "sell" | "hold"
    confidence: float = 0.5
    detail: dict[str, Any] | None = None

@dataclass
class OrderIntent:
    side: str  # "buy" | "sell"
    order_type: str = "market"
    quote_amount: float | None = None          # for buys
    sell_base_amount: float | None = None      # for sells
    reason: str | None = None
    meta: dict[str, Any] | None = None

class Strategy(Protocol):
    name: str

    def compute_signal(self, *, cfg: dict, market: MarketContext, position: PositionContext) -> Signal: ...
    def suggest_orders(self, *, cfg: dict, market: MarketContext, position: PositionContext, signal: Signal) -> list[OrderIntent]: ...
