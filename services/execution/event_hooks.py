from __future__ import annotations
from typing import Any, Dict, Optional
from services.execution.event_log import log_event

def log_cancel_requested(venue: str, symbol: str, order_id: str, reason: str | None = None) -> str:
    return log_event(venue, symbol, "cancel_requested", ref_id=str(order_id), payload={"reason": reason})

def log_cancel_result(venue: str, symbol: str, order_id: str, ok: bool, details: dict | None = None) -> str:
    return log_event(venue, symbol, "cancel_result", ref_id=str(order_id), payload={"ok": bool(ok), "details": details or {}})

def log_replace_requested(venue: str, symbol: str, order_id: str, new_price: float | None = None, new_qty: float | None = None) -> str:
    return log_event(venue, symbol, "replace_requested", ref_id=str(order_id), payload={"new_price": new_price, "new_qty": new_qty})

def log_replace_result(venue: str, symbol: str, order_id: str, ok: bool, details: dict | None = None) -> str:
    return log_event(venue, symbol, "replace_result", ref_id=str(order_id), payload={"ok": bool(ok), "details": details or {}})
