from __future__ import annotations

from services.markets.symbols import (
    binance_native,
    canonicalize,
    coinbase_native,
    gate_native,
    normalize_symbol as _normalize_symbol,
)


def normalize_symbol(symbol: str, venue: str | None = None) -> str:
    return _normalize_symbol(str(symbol or ""), venue=venue, out="slash")


__all__ = [
    "binance_native",
    "canonicalize",
    "coinbase_native",
    "gate_native",
    "normalize_symbol",
]
