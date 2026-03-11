from __future__ import annotations

from typing import Any, Dict

from services.market_data.tick_reader import get_best_bid_ask_last, mid_price
from services.market_data.symbol_router import map_symbol
from services.security.exchange_factory import make_exchange


def probe_price(venue: str, symbol: str, *, allow_network: bool = False) -> Dict[str, Any]:
    v = str(venue).lower().strip()
    s = str(symbol).strip()

    q = get_best_bid_ask_last(v, s)
    if q:
        return {"ok": True, "source": "snapshot", "venue": v, "symbol": s, "quote": q, "mid": mid_price(q)}

    if not allow_network:
        return {"ok": False, "reason": "no_snapshot_quote", "venue": v, "symbol": s}

    ex = None
    try:
        ex = make_exchange(v, {"apiKey": None, "secret": None}, enable_rate_limit=True)
        native = map_symbol(v, s)
        t = ex.fetch_ticker(native)
        q2 = {
            "ts_ms": int(t.get("timestamp") or 0),
            "bid": t.get("bid"),
            "ask": t.get("ask"),
            "last": t.get("last"),
        }
        return {"ok": True, "source": "network", "venue": v, "symbol": s, "native_symbol": native, "quote": q2, "mid": mid_price(q2)}
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}", "venue": v, "symbol": s}
    finally:
        try:
            if ex is not None and hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass
