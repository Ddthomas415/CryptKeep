"""Fixed, fail-closed age policy for paper buys (independent of live TTL)."""
from __future__ import annotations

from typing import Any

from services.execution.intent_ttl import _parse_created_epoch


PAPER_BUY_CREATED_TS = "paper_buy_created_ts"
PAPER_BUY_MAX_AGE_S = 120.0


def buy_age_verdict(created_ts: Any, now_ts: Any) -> dict[str, Any]:
    """Accept only a known non-future creation age strictly below 120 seconds."""
    out = {"ok": False, "reason": "paper_buy_ttl:invalid_now", "age_s": None}

    def epoch(value):
        if isinstance(value, bool):
            return None
        try:
            return _parse_created_epoch(value)
        except (TypeError, ValueError, OverflowError, OSError):
            return None

    now = epoch(now_ts)
    if now is None:
        return out
    if created_ts is None or (isinstance(created_ts, str) and not created_ts.strip()):
        out["reason"] = "paper_buy_ttl:missing_created_ts"
        return out
    created = epoch(created_ts)
    if created is None:
        out["reason"] = "paper_buy_ttl:invalid_created_ts"
        return out
    age = now - created
    out["age_s"] = age
    if age < 0:
        out["reason"] = "paper_buy_ttl:future_created_ts"
    elif age >= PAPER_BUY_MAX_AGE_S:
        out["reason"] = "paper_buy_ttl:expired"
    else:
        out.update(ok=True, reason="ok")
    return out
