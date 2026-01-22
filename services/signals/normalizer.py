from __future__ import annotations
from typing import Any, Dict, Optional
from services.signals.models import SignalEvent, new_id, utc_now_iso
from services.market_data.symbol_router import normalize_symbol, normalize_venue

def _f(x, default=0.0):
    try:
        v = float(x)
        if v != v:
            return default
        return v
    except Exception:
        return default

def normalize_signal(payload: Dict[str, Any]) -> SignalEvent:
    symbol = normalize_symbol(str(payload.get("symbol") or payload.get("pair") or "").strip())
    action = str(payload.get("action") or payload.get("side") or "").lower().strip()
    if action not in ("buy","sell","hold"):
        if action in ("long","enter_long"):
            action = "buy"
        elif action in ("short","enter_short"):
            action = "sell"
        else:
            action = "hold"
    source = str(payload.get("source") or "webhook").strip()
    author = str(payload.get("author") or payload.get("trader") or "unknown").strip()
    venue_hint = str(payload.get("venue") or payload.get("exchange") or payload.get("venue_hint") or "").strip()
    venue_hint = normalize_venue(venue_hint) if venue_hint else ""
    confidence = _f(payload.get("confidence"), 0.5)
    if confidence < 0: confidence = 0.0
    if confidence > 1: confidence = 1.0
    ts = str(payload.get("ts") or payload.get("timestamp") or payload.get("time") or utc_now_iso())
    notes = str(payload.get("notes") or payload.get("comment") or payload.get("message") or "").strip()
    return SignalEvent(
        signal_id=str(payload.get("signal_id") or new_id()),
        ts=ts,
        source=source,
        author=author,
        venue_hint=venue_hint,
        symbol=symbol,
        action=action,  # type: ignore
        confidence=confidence,
        notes=notes,
        raw=dict(payload),
    )
