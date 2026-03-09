from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.markets.symbols import canonicalize
from storage.signal_inbox_sqlite import SignalInboxSQLite
from storage.signal_reliability_sqlite import SignalReliabilitySQLite


def _parse_ts(ts: Any) -> float | None:
    try:
        text = str(ts or "").strip()
        if not text:
            return None
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _clamp(x: Any, default: float = 0.5) -> float:
    try:
        val = float(x)
    except Exception:
        val = float(default)
    return max(0.0, min(1.0, val))


def _direction(action: str) -> float:
    text = str(action or "").strip().lower()
    if text == "buy":
        return 1.0
    if text == "sell":
        return -1.0
    return 0.0


def compute_consensus(
    *,
    symbols: list[str],
    lookback_signals: int = 500,
    max_signal_age_sec: int = 21600,
    min_weight: float = 0.0,
    lookback_evals: int = 500,
    min_evals: int = 5,
) -> dict[str, Any]:
    inbox = SignalInboxSQLite()
    reliability = SignalReliabilitySQLite()
    now = time.time()
    min_weight = max(0.0, float(min_weight or 0.0))
    out: dict[str, Any] = {"ok": True, "consensus": {}}

    for symbol in symbols or []:
        sym = canonicalize(str(symbol or ""))
        rel_rows = reliability.list(limit=int(lookback_evals), symbol=sym)
        rel_map: dict[tuple[str, str], dict[str, Any]] = {}
        for row in rel_rows:
            key = (str(row.get("source") or ""), str(row.get("author") or ""))
            prev = rel_map.get(key)
            if prev is None or str(row.get("updated_ts") or "") > str(prev.get("updated_ts") or ""):
                rel_map[key] = row

        signals = inbox.list_signals(limit=int(lookback_signals), symbol=sym)
        total = 0.0
        weight_sum = 0.0
        contributors: set[tuple[str, str]] = set()
        used = 0

        for sig in signals:
            ts_epoch = _parse_ts(sig.get("ts"))
            if ts_epoch is None or (now - ts_epoch) > float(max_signal_age_sec):
                continue
            direction = _direction(str(sig.get("action") or ""))
            if direction == 0.0:
                continue

            source = str(sig.get("source") or "")
            author = str(sig.get("author") or "")
            rel = rel_map.get((source, author))
            rel_weight = 0.5
            if rel and int(rel.get("n_scored") or 0) >= int(min_evals):
                rel_weight = _clamp(rel.get("hit_rate"), default=0.5)
            confidence = _clamp(sig.get("confidence"), default=0.5)
            weight = max(min_weight, confidence * rel_weight)
            total += direction * weight
            weight_sum += weight
            contributors.add((source, author))
            used += 1

        score = (total / weight_sum) if weight_sum > 0 else 0.0
        out["consensus"][sym] = {
            "score": float(score),
            "count": int(used),
            "contributors": int(len(contributors)),
            "weight_sum": float(weight_sum),
        }

    return out
