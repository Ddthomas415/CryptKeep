from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Optional

@dataclass(frozen=True)
class ParsedSymbol:
    base: str
    quote: str

def _coerce_venue(v: Optional[str]) -> str:
    return str(v or "").lower().strip()

def _first_from_csv(s: str) -> str:
    s = str(s or "").strip()
    if not s:
        return ""
    return s.split(",")[0].strip()

def parse_symbol(sym: str) -> Optional[ParsedSymbol]:
    sym = _first_from_csv(sym)
    if not sym:
        return None

    for sep in ("/", "-", "_"):
        if sep in sym:
            a, b = sym.split(sep, 1)
            a, b = a.strip().upper(), b.strip().upper()
            if a and b:
                return ParsedSymbol(a, b)
    return None

def default_quote_for_venue(venue: Optional[str]) -> str:
    v = _coerce_venue(venue)
    if v.startswith("coinbase"):
        return "USD"
    return "USDT"

def normalize_symbol(sym: str, *, venue: Optional[str] = None, out: str = "slash") -> str:
    v = _coerce_venue(venue)
    out = (out or "slash").lower().strip()
    parsed = parse_symbol(sym)

    if parsed is None:
        base, quote = "BTC", default_quote_for_venue(v)
    else:
        base, quote = parsed.base, parsed.quote

    sep = "/" if out == "slash" else "-"
    return f"{base}{sep}{quote}"

def canonicalize(symbol: str, venue: str | None = None) -> str:
    """Return canonical hyphenated symbol (e.g., 'BTC-USD', 'BTC-USDT').

    Accepts inputs like 'btc/usd', 'BTC_USD', 'BTC-USD'.
    `venue` is kept for API compatibility but not required for normalization.
    """
    if symbol is None:
        return ""
    sym = str(symbol).strip().upper()
    sym = sym.replace("/", "-").replace("_", "-")
    while "--" in sym:
        sym = sym.replace("--", "-")
    return sym

def env_symbol(*, venue: Optional[str] = None, out: str = "slash") -> str:
    sym = os.environ.get("CBP_SYMBOLS") or os.environ.get("CBP_TRADE_SYMBOL") or ""
    return normalize_symbol(sym or "", venue=venue, out=out)


def _split_canonical(symbol: str) -> tuple[str, str]:
    normalized = canonicalize(symbol)
    if "-" not in normalized:
        return normalized, ""
    head, tail = normalized.split("-", 1)
    return head, tail


def binance_native(symbol: str) -> str:
    base, quote = _split_canonical(symbol)
    return f"{base}{quote}" if quote else base


def gate_native(symbol: str) -> str:
    base, quote = _split_canonical(symbol)
    return f"{base}_{quote}" if quote else base


def coinbase_native(symbol: str) -> str:
    return canonicalize(symbol)
