"""
Alternative data sources.
- Fear & Greed Index (alternative.me — free, no key needed)
- Funding rates (ccxt binance futures)
"""
from __future__ import annotations
import json, time
from typing import Any
import urllib.request


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


def get_funding_rates(
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    """
    Fetch perpetual futures funding rates from Binance.
    Positive rate = longs pay shorts (overbought).
    Negative rate = shorts pay longs (oversold).
    Threshold: >0.05% = elevated longs, <-0.01% = elevated shorts.
    """
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
        rates = []
        for sym in target:
            try:
                info = ex.fetch_funding_rate(sym)
                rate = float(info.get("fundingRate") or 0.0) * 100.0

                if rate > 0.05:    signal = "overleveraged_longs"
                elif rate < -0.01: signal = "overleveraged_shorts"
                elif rate > 0.02:  signal = "elevated_longs"
                else:              signal = "neutral"

                rates.append({
                    "symbol":     sym,
                    "rate_pct":   round(rate, 4),
                    "annualized": round(rate * 3 * 365, 2),
                    "signal":     signal,
                })
            except Exception:
                pass
        ex.close()
        return {
            "ok":    True,
            "rates": rates,
            "ts":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}:{e}", "rates": []}


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
