from __future__ import annotations

from typing import Iterable

from services.markets.symbols import normalize_symbol as _normalize_symbol


def normalize_symbol(symbol: str, venue: str | None = None) -> str:
    return _normalize_symbol(str(symbol or ""), venue=venue, out="slash")


def normalize_symbols(symbols: Iterable[str], venue: str | None = None) -> dict[str, list[str] | int]:
    normalized: list[str] = []
    invalid: list[str] = []
    for symbol in symbols or []:
        raw = str(symbol or "").strip()
        if not raw:
            invalid.append(raw)
            continue
        value = normalize_symbol(raw, venue=venue)
        if not value:
            invalid.append(raw)
            continue
        if value not in normalized:
            normalized.append(value)
    return {"normalized": normalized, "invalid": invalid, "count": len(normalized)}
