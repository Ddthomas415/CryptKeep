from __future__ import annotations

import math
import time
from typing import Any

from dashboard.services.coinbase_movers import fetch_coinbase_movers
from dashboard.services.view_data import _get_market_snapshot, _load_local_ohlcv


PUMP_THRESHOLD_PCT = 10.0
DUMP_THRESHOLD_PCT = -10.0
VOLUME_SURGE_MIN = 1.5


def _safe(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _scan_from_local_watchlist(*, venue: str, symbols: list[str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for asset in symbols:
        try:
            snapshot = _get_market_snapshot(asset, exchange=venue) or {}

            last = _safe(snapshot.get("last_price"), 0.0)
            high = _safe(snapshot.get("high"), 0.0)
            low = _safe(snapshot.get("low"), 0.0)
            volume_24h = _safe(snapshot.get("volume_24h"), 0.0)
            change_pct = _safe(snapshot.get("change_pct"), 0.0)

            volatility_pct = ((high - low) / last * 100.0) if last > 0 else 0.0

            candles_1h = _load_local_ohlcv(venue, asset, timeframe="1h", limit=48) or []
            closes = [float(c[4]) for c in candles_1h if len(c) > 4 and c[4] is not None]
            rsi_val = _rsi(closes)

            candles_1d = _load_local_ohlcv(venue, asset, timeframe="1d", limit=5) or []
            volume_surge = 1.0
            if len(candles_1d) >= 4:
                recent = _safe(candles_1d[-1][5]) if len(candles_1d[-1]) > 5 else 0.0
                prior = [_safe(row[5]) for row in candles_1d[-4:-1] if len(row) > 5]
                avg = (sum(prior) / len(prior)) if prior else 0.0
                volume_surge = (recent / avg) if avg > 0 else 1.0

            signal = "neutral"
            if change_pct >= PUMP_THRESHOLD_PCT:
                signal = "pump"
            elif change_pct <= DUMP_THRESHOLD_PCT:
                signal = "dump"
            elif rsi_val is not None and rsi_val < 30:
                signal = "oversold"
            elif rsi_val is not None and rsi_val > 70:
                signal = "overbought"

            results.append({
                "symbol": asset,
                "last": round(last, 6) if last else 0.0,
                "change_pct": round(change_pct, 2),
                "volume_24h": round(volume_24h, 2),
                "volume_surge": round(volume_surge, 2),
                "volatility_pct": round(volatility_pct, 2),
                "rsi": round(rsi_val, 1) if rsi_val is not None else None,
                "high": high,
                "low": low,
                "signal": signal,
                "snapshot_source": str(snapshot.get("source") or ""),
                "snapshot_timestamp": str(snapshot.get("timestamp") or ""),
            })
        except Exception as exc:
            results.append({
                "symbol": asset,
                "error": f"{type(exc).__name__}:{exc}",
                "signal": "error",
            })

    valid = [r for r in results if "error" not in r]

    pumps = sorted(
        [r for r in valid if r["change_pct"] >= PUMP_THRESHOLD_PCT],
        key=lambda r: r["change_pct"],
        reverse=True,
    )
    dumps = sorted(
        [r for r in valid if r["change_pct"] <= DUMP_THRESHOLD_PCT],
        key=lambda r: r["change_pct"],
    )
    volume_surges = sorted(
        [r for r in valid if r["volume_surge"] >= VOLUME_SURGE_MIN],
        key=lambda r: r["volume_surge"],
        reverse=True,
    )
    oversold = sorted(
        [r for r in valid if r.get("rsi") is not None and r["rsi"] < 30],
        key=lambda r: r["rsi"],
    )

    return {
        "ok": True,
        "runner_ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scanned": len(results),
        "requested": len(symbols),
        "source": "local_watchlist",
        "pumps": pumps,
        "dumps": dumps,
        "volume_surges": volume_surges,
        "oversold": oversold,
        "all": sorted(valid, key=lambda r: abs(r["change_pct"]), reverse=True),
        "errors": [r for r in results if "error" in r],
    }


def _scan_from_coinbase_movers(*, limit: int = 200) -> dict[str, Any]:
    movers = fetch_coinbase_movers(limit=limit)
    if not movers.get("ok"):
        return {
            "ok": False,
            "runner_ok": False,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scanned": 0,
            "requested": 0,
            "source": "coinbase_movers",
            "pumps": [],
            "dumps": [],
            "volume_surges": [],
            "oversold": [],
            "all": [],
            "errors": movers.get("errors", []) or [{"error": "coinbase_movers_failed"}],
        }

    all_rows = list(movers.get("all") or [])

    normalized: list[dict[str, Any]] = []
    for row in all_rows:
        symbol = str(row.get("symbol") or "")
        last = _safe(row.get("last"), 0.0)
        high = _safe(row.get("high"), 0.0)
        low = _safe(row.get("low"), 0.0)

        change_pct = _safe(row.get("change_pct"), 0.0)
        volume_24h = _safe(row.get("volume_24h"), _safe(row.get("quote_volume"), 0.0))
        volatility_pct = _safe(row.get("volatility_pct"), 0.0)

        if not volatility_pct and last > 0 and high > 0 and low > 0:
            volatility_pct = ((high - low) / last) * 100.0

        signal = "neutral"
        if change_pct >= PUMP_THRESHOLD_PCT:
            signal = "pump"
        elif change_pct <= DUMP_THRESHOLD_PCT:
            signal = "dump"

        normalized.append({
            "symbol": symbol,
            "last": round(last, 6) if last else 0.0,
            "change_pct": round(change_pct, 2),
            "volume_24h": round(volume_24h, 2),
            "volume_surge": _safe(row.get("volume_surge"), 1.0),
            "volatility_pct": round(volatility_pct, 2),
            "rsi": row.get("rsi"),
            "high": high,
            "low": low,
            "signal": signal,
            "snapshot_source": "coinbase_movers",
            "snapshot_timestamp": str(movers.get("ts") or ""),
        })

    pumps = sorted(
        [r for r in normalized if r["change_pct"] >= PUMP_THRESHOLD_PCT],
        key=lambda r: r["change_pct"],
        reverse=True,
    )
    dumps = sorted(
        [r for r in normalized if r["change_pct"] <= DUMP_THRESHOLD_PCT],
        key=lambda r: r["change_pct"],
    )
    volume_surges = sorted(
        normalized,
        key=lambda r: r["volume_24h"],
        reverse=True,
    )[:50]
    oversold = [
        r for r in normalized
        if r.get("rsi") is not None and _safe(r.get("rsi"), 100.0) < 30.0
    ]
    oversold = sorted(oversold, key=lambda r: _safe(r.get("rsi"), 100.0))

    return {
        "ok": True,
        "runner_ok": True,
        "ts": str(movers.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
        "scanned": int(movers.get("scanned", len(normalized))),
        "requested": int(movers.get("scanned", len(normalized))),
        "source": "coinbase_movers",
        "pumps": pumps,
        "dumps": dumps,
        "volume_surges": volume_surges,
        "oversold": oversold,
        "all": normalized,
        "errors": list(movers.get("errors") or []),
        "gainers": list(movers.get("gainers") or []),
        "losers": list(movers.get("losers") or []),
        "most_active": list(movers.get("most_active") or []),
        "most_volatile": list(movers.get("most_volatile") or []),
    }


def run_symbol_scan(*, venue: str = "coinbase", symbols: list[str]) -> dict[str, Any]:
    if venue == "coinbase":
        return _scan_from_coinbase_movers(limit=200)
    return _scan_from_local_watchlist(venue=venue, symbols=symbols)
