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


def get_open_interest_snapshot(
    *,
    symbols: list[str] | None = None,
    venue: str = "binance",
) -> dict[str, Any]:
    if ccxt is None:
        return {"ok": False, "reason": "ccxt_unavailable", "rows": []}

    target = symbols or ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "LINK/USDT"]
    ex_cls = getattr(ccxt, venue, None)
    if ex_cls is None:
        return {"ok": False, "reason": f"unknown_venue:{venue}", "rows": []}

    ex = ex_cls({"enableRateLimit": True, "options": {"defaultType": "future"}})
    rows: list[dict[str, Any]] = []
    try:
        for symbol in target:
            try:
                if hasattr(ex, "fetch_open_interest"):
                    oi = ex.fetch_open_interest(symbol)
                    open_interest = _safe_float(oi.get("openInterest"), 0.0)
                    rows.append({
                        "symbol": symbol,
                        "open_interest": round(open_interest, 4),
                        "raw": oi,
                    })
            except Exception:
                continue

        rows.sort(key=lambda r: r["open_interest"], reverse=True)
        return {
            "ok": True,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "venue": venue,
            "rows": rows,
        }
    finally:
        try:
            ex.close()
        except Exception:
            pass


def get_liquidation_risk_levels(
    *,
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    target = symbols or ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    rows = []
    for symbol in target:
        rows.append({
            "symbol": symbol,
            "long_liq_cluster": None,
            "short_liq_cluster": None,
            "risk_note": "scaffold_only_no_live_liquidation_feed",
        })
    return {
        "ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": rows,
    }


def get_social_sentiment_snapshot(
    *,
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    target = symbols or ["BTC", "ETH", "SOL", "AVAX", "LINK"]
    rows = []
    for symbol in target:
        rows.append({
            "symbol": symbol,
            "sentiment_score": None,
            "source": "scaffold_only_no_social_feed",
            "note": "placeholder_for_twitter_reddit_signal",
        })
    return {
        "ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": rows,
    }


def build_market_intelligence_snapshot(
    *,
    futures_symbols: list[str] | None = None,
    spot_symbols: list[str] | None = None,
) -> dict[str, Any]:
    oi = get_open_interest_snapshot(symbols=futures_symbols)
    liq = get_liquidation_risk_levels(symbols=futures_symbols)
    social = get_social_sentiment_snapshot(
        symbols=[s.split("/")[0] for s in (spot_symbols or ["BTC/USD", "ETH/USD", "SOL/USD"])]
    )

    return {
        "ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "open_interest": oi,
        "liquidation": liq,
        "social_sentiment": social,
    }
