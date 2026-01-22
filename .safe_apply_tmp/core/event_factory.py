from __future__ import annotations

from typing import Any, Dict

from core.events import (
    BookEvent,
    CandleEvent,
    EventBase,
    FundingEvent,
    OpenInterestEvent,
    SignalEvent,
    TradeEvent,
)

_EVENT_MAP = {
    "trade": TradeEvent,
    "book_l2": BookEvent,
    "candle": CandleEvent,
    "funding": FundingEvent,
    "open_interest": OpenInterestEvent,
    "signal": SignalEvent,
}


def event_from_dict(d: Dict[str, Any]) -> EventBase:
    et = d.get("event_type")
    cls = _EVENT_MAP.get(et)
    if cls is None:
        raise ValueError(f"Unknown event_type: {et!r}")
    return cls.model_validate(d)
