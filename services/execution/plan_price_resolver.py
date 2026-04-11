
from __future__ import annotations

import math
import time
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
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
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
                source = "last"
                if px <= 0:
                    bid = _safe_float(ticker.get("bid"), 0.0)
                    ask = _safe_float(ticker.get("ask"), 0.0)
                    px = bid or ask
                    source = "bid_or_ask"
                if px > 0:
                    out[sym] = {
                        "price": px,
                        "venue": venue,
                        "price_source": source,
                        "price_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
            except Exception:
                continue
    finally:
        try:
            ex.close()
        except Exception:
            pass

    return out
