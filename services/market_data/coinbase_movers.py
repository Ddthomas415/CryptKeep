from __future__ import annotations

import math
import time
from typing import Any

import ccxt


def _safe(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _is_usd_spot_market(market: dict[str, Any]) -> bool:
    quote = str(market.get("quote") or "")
    active = bool(market.get("active", False))
    spot = bool(market.get("spot", False))
    return active and spot and quote in {"USD", "USDC"}


def fetch_coinbase_movers(limit: int = 25, batch_size: int = 75) -> dict[str, Any]:
    ex = ccxt.coinbase({"enableRateLimit": True})
    errors: list[dict[str, Any]] = []

    try:
        markets = ex.load_markets()
        symbols = [symbol for symbol, meta in markets.items() if _is_usd_spot_market(meta)]

        tickers: dict[str, Any] = {}
        for batch in _chunks(symbols, batch_size):
            try:
                partial = ex.fetch_tickers(batch)
                if partial:
                    tickers.update(partial)
            except Exception as exc:
                errors.append({
                    "batch_size": len(batch),
                    "symbols_preview": batch[:5],
                    "error": f"{type(exc).__name__}:{exc}",
                })

        rows: list[dict[str, Any]] = []
        for symbol in symbols:
            t = tickers.get(symbol) or {}
            if not t:
                continue

            last = _safe(t.get("last"), 0.0)
            high = _safe(t.get("high"), 0.0)
            low = _safe(t.get("low"), 0.0)
            percentage = _safe(t.get("percentage"), 0.0)
            quote_volume = _safe(t.get("quoteVolume"), 0.0)
            base_volume = _safe(t.get("baseVolume"), 0.0)

            volatility_pct = ((high - low) / last * 100.0) if last > 0 else 0.0

            rows.append({
                "symbol": symbol,
                "last": round(last, 8),
                "high": round(high, 8),
                "low": round(low, 8),
                "change_pct": round(percentage, 2),
                "quote_volume": round(quote_volume, 2),
                "base_volume": round(base_volume, 8),
                "volume_24h": round(quote_volume, 2),
                "volatility_pct": round(volatility_pct, 2),
            })

        gainers = sorted(rows, key=lambda r: r["change_pct"], reverse=True)[:limit]
        losers = sorted(rows, key=lambda r: r["change_pct"])[:limit]
        most_active = sorted(rows, key=lambda r: r["quote_volume"], reverse=True)[:limit]
        most_volatile = sorted(rows, key=lambda r: r["volatility_pct"], reverse=True)[:limit]
        all_ranked = sorted(rows, key=lambda r: abs(r["change_pct"]), reverse=True)

        return {
            "ok": True,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scanned": len(rows),
            "gainers": gainers,
            "losers": losers,
            "most_active": most_active,
            "most_volatile": most_volatile,
            "all": all_ranked,
            "errors": errors,
        }
    finally:
        try:
            ex.close()
        except Exception:
            pass
