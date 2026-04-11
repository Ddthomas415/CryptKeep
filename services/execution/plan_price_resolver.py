from __future__ import annotations

import math
from typing import Any

try:
    import ccxt
except Exception:
    ccxt = None


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def resolve_prices(
    *,
    symbols: list[str],
    venue: str = "coinbase",
) -> dict[str, float]:
    out: dict[str, float] = {}
    if ccxt is None:
        return out

    ex_cls = getattr(ccxt, venue, None)
    if ex_cls is None:
        return out

    ex = ex_cls({"enableRateLimit": True})
    try:
        for symbol in symbols:
            sym = str(symbol or "").strip().upper()
            if not sym:
                continue
            try:
                ticker = ex.fetch_ticker(sym)
                px = _safe_float(ticker.get("last"), 0.0)
                if px <= 0:
                    px = _safe_float(ticker.get("bid"), 0.0) or _safe_float(ticker.get("ask"), 0.0)
                if px > 0:
                    out[sym] = px
            except Exception:
                continue
    finally:
        try:
            ex.close()
        except Exception:
            pass

    return out
