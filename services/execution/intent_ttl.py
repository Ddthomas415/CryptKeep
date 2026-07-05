"""
Intent age (TTL) checks for live/shadow intent consumers.

Substrate backlog #18: consumers check market snapshot freshness but not the
intent's own age, so a restart after hours or days could submit an intent
sized and justified by stale context at current prices.

Fail-closed contract: an intent whose age cannot be determined (missing,
unparseable, non-finite, or future-dated ``created_ts``) must not be
submitted. The window env override falls back to the strict default on any
non-finite or non-positive value.
"""
from __future__ import annotations

import math
import os
import time
from datetime import datetime, timezone
from typing import Any

INTENT_MAX_AGE_ENV = "CBP_MAX_INTENT_AGE_SEC"
INTENT_MAX_AGE_S_DEFAULT = 300.0
_INTENT_FUTURE_SKEW_S = 60.0


def max_intent_age_s() -> float:
    """
    Bounded intent age window. Invalid, empty, non-finite, or non-positive
    env overrides fall back to the strict default instead of widening or
    disabling the window.
    """
    raw = os.environ.get(INTENT_MAX_AGE_ENV)
    if raw is None or str(raw).strip() == "":
        return INTENT_MAX_AGE_S_DEFAULT
    try:
        value = float(raw)
    except Exception as _err:
        return INTENT_MAX_AGE_S_DEFAULT
    if not math.isfinite(value) or value <= 0.0:
        return INTENT_MAX_AGE_S_DEFAULT
    return value


def _parse_created_epoch(created_ts: Any) -> float | None:
    """
    Parse an intent ``created_ts`` into a UTC epoch. Returns ``None`` when the
    value is missing or unusable (caller treats that as fail-closed).
    Naive timestamps are treated as UTC because the queue writes
    ``datetime.now(timezone.utc).isoformat()``.
    """
    if created_ts is None:
        return None
    if isinstance(created_ts, (int, float)):
        value = float(created_ts)
        return value if math.isfinite(value) and value > 0.0 else None
    raw = str(created_ts).strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except Exception as _err:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    epoch = dt.timestamp()
    return epoch if math.isfinite(epoch) and epoch > 0.0 else None


def check_intent_age(created_ts: Any, *, now_epoch: float | None = None) -> dict[str, Any]:
    """
    Return ``{"ok", "reason", "age_s", "max_age_s"}`` for one intent.

    Reasons (all fail closed except ``ok``):
      - ``intent_ttl:missing_created_ts``
      - ``intent_ttl:invalid_created_ts``
      - ``intent_ttl:invalid_now``
      - ``intent_ttl:future_created_ts``
      - ``intent_ttl:expired:<age>s``
    """
    max_age = max_intent_age_s()
    out: dict[str, Any] = {
        "ok": False,
        "reason": "intent_ttl:missing_created_ts",
        "age_s": None,
        "max_age_s": max_age,
    }
    try:
        now = float(now_epoch) if now_epoch is not None else float(time.time())
    except Exception as _err:
        now = 0.0
    if not math.isfinite(now) or now <= 0.0:
        out["reason"] = "intent_ttl:invalid_now"
        return out
    if created_ts is None or (isinstance(created_ts, str) and not created_ts.strip()):
        return out
    epoch = _parse_created_epoch(created_ts)
    if epoch is None:
        out["reason"] = "intent_ttl:invalid_created_ts"
        return out
    age_s = now - epoch
    out["age_s"] = age_s
    if age_s < -_INTENT_FUTURE_SKEW_S:
        out["reason"] = "intent_ttl:future_created_ts"
        return out
    if age_s > max_age:
        out["reason"] = f"intent_ttl:expired:{age_s:.0f}s"
        return out
    out["ok"] = True
    out["reason"] = "ok"
    return out
