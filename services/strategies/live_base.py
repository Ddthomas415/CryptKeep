from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class LiveContext:
    venue: str
    symbol: str
    base: str
    quote: str
    bucket: str
    last_price: float
    last_candle_ts: str
    position_qty: float

@dataclass
class LiveDecision:
    action: str
    side: str | None = None
    reason: str = ""
    meta: dict[str, Any] | None = None

class LiveStrategy:
    name: str = "base"

    def decide(self, df, ctx: LiveContext) -> LiveDecision:
        raise NotImplementedError
