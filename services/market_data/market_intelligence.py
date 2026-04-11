from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

try:
    import ccxt
except Exception:
    ccxt = None

from services.market_data.alternative_data import get_funding_rates


STATE_DIR = Path(".cbp_state/runtime/market_intelligence")
OI_PREV_FILE = STATE_DIR / "open_interest_prev.json"


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def _load_prev_oi() -> dict[str, float]:
    try:
        if OI_PREV_FILE.exists():
            data = json.loads(OI_PREV_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): _safe_float(v, 0.0) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _save_prev_oi(rows: list[dict[str, Any]]) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {str(r.get("symbol") or ""): _safe_float(r.get("open_interest"), 0.0) for r in rows}
        OI_PREV_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


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

    prev_map = _load_prev_oi()
    ex = ex_cls({"enableRateLimit": True, "options": {"defaultType": "future"}})
    rows: list[dict[str, Any]] = []
    try:
        for symbol in target:
            try:
                if not hasattr(ex, "fetch_open_interest"):
                    continue
                oi = ex.fetch_open_interest(symbol)
                ticker = ex.fetch_ticker(symbol)
                open_interest = _safe_float(oi.get("openInterest"), 0.0)
                prev_oi = _safe_float(prev_map.get(symbol), 0.0)
                oi_change_pct = ((open_interest - prev_oi) / prev_oi * 100.0) if prev_oi > 0 else 0.0
                price_change_pct = _safe_float(ticker.get("percentage"), 0.0)

                rows.append({
                    "symbol": symbol,
                    "open_interest": round(open_interest, 4),
                    "open_interest_prev": round(prev_oi, 4),
                    "oi_change_pct": round(oi_change_pct, 4),
                    "price_change_pct": round(price_change_pct, 4),
                    "raw": oi,
                })
            except Exception:
                continue

        rows.sort(key=lambda r: abs(_safe_float(r.get("oi_change_pct"), 0.0)), reverse=True)
        _save_prev_oi(rows)

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
    funding = get_funding_rates(symbols=futures_symbols)
    liq = get_liquidation_risk_levels(symbols=futures_symbols)
    social = get_social_sentiment_snapshot(
        symbols=[s.split("/")[0] for s in (spot_symbols or ["BTC/USD", "ETH/USD", "SOL/USD"])]
    )

    return {
        "ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "open_interest": oi,
        "funding": funding,
        "liquidation": liq,
        "social_sentiment": social,
    }
