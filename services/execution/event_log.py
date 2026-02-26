from __future__ import annotations


def log_event(venue: str, symbol: str, event: str, *, ref_id: str | None = None, payload: dict | None = None) -> str:
    return f"{venue}/{symbol}:{event}:{ref_id}"
