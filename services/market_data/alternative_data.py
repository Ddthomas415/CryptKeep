"""
Alternative data sources.
- Fear & Greed Index (alternative.me — free, no key needed)
- Funding rates (ccxt binance futures)
"""
from __future__ import annotations
import json, time
from datetime import datetime, timezone
from typing import Any
import urllib.request

from services.analytics.funding_observations import finite_number, observation


def _get_json(url: str, timeout: int = 10) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CryptKeep/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def get_fear_greed() -> dict[str, Any]:
    """
    Returns current Fear & Greed index (0-100).
    0-24 = Extreme Fear, 25-49 = Fear, 50-74 = Greed, 75-100 = Extreme Greed.
    """
    data = _get_json("https://api.alternative.me/fng/?limit=2")
    if not data or not data.get("data"):
        return {"ok": False, "reason": "fetch_failed", "value": 50, "regime": "unknown"}

    latest = data["data"][0]
    prev   = data["data"][1] if len(data["data"]) > 1 else {}
    value  = int(latest.get("value", 50))
    label  = str(latest.get("value_classification", "Neutral"))
    prev_v = int(prev.get("value", value)) if prev else value

    if value <= 20:   regime = "extreme_fear"
    elif value <= 40: regime = "fear"
    elif value >= 80: regime = "extreme_greed"
    elif value >= 60: regime = "greed"
    else:             regime = "neutral"

    signal = "buy_zone" if value <= 25 else ("sell_zone" if value >= 75 else "neutral")

    return {
        "ok":      True,
        "value":   value,
        "label":   label,
        "regime":  regime,
        "prev":    prev_v,
        "change":  value - prev_v,
        "signal":  signal,
        "ts":      str(latest.get("timestamp", "")),
    }


def _funding_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_funding_rates(
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    """
    Fetch public funding observations, not qualified normalized signals.

    A provider's per-print rate, effective interval and crowding basis must
    not be silently equated with an eight-hour rate. Raw evidence is retained.
    """
    ex = None
    rates = []
    errors = []
    try:
        import ccxt
        ex = ccxt.binance({
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        })
        target = symbols or [
            "BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT",
            "DOGE/USDT", "LINK/USDT", "MATIC/USDT", "ADA/USDT",
        ]
        for sym in target:
            try:
                started = _funding_utc_now()
                info = ex.fetch_funding_rate(sym)
                received = _funding_utc_now()
                record = observation(
                    venue="binance", symbol=sym, captured_at=received, payload=info,
                    receipt={"request_started_at": started, "received_at": received,
                             "requested_symbol": sym, "fetch_method": "fetch_funding_rate"})
                raw_rate = record["funding_rate"]
                raw_pct = finite_number(raw_rate * 100.0) if raw_rate is not None else None
                rates.append({
                    "symbol": sym, "raw_rate_pct": raw_pct,
                    "raw_percent_unrepresentable": raw_rate is not None and raw_pct is None,
                    "rate_pct": None, "annualized": None, "signal": "unknown",
                    "normalization_eligible": False,
                    "normalization_reason": record["normalization"]["reason"],
                    "observation": record,
                })
            except Exception as exc:
                errors.append({"symbol": sym, "reason": f"funding_observation_failed:{type(exc).__name__}"})
    except Exception as exc:
        errors.append({"reason": f"funding_setup_failed:{type(exc).__name__}"})
    finally:
        if ex is not None:
            try:
                ex.close()
            except Exception as exc:
                errors.append({"reason": f"funding_close_failed:{type(exc).__name__}"})
    return {"ok": bool(rates), "complete": not errors, "rates": rates, "errors": errors,
            "normalization_eligible": False,
            "reason": "observed_unverified" if rates else "funding_unavailable",
            "ts": _funding_utc_now()}


def get_market_regime() -> dict[str, Any]:
    """Combined snapshot: fear/greed + funding signal."""
    fg = get_fear_greed()
    return {
        "ok":         True,
        "ts":         time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fear_greed": fg,
        "regime":     fg.get("regime", "unknown"),
        "signal":     fg.get("signal", "neutral"),
        "fg_value":   fg.get("value", 50),
    }
