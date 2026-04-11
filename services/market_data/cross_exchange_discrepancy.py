from __future__ import annotations

import math
import time
from typing import Any

import ccxt


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def scan_cross_exchange_discrepancies(
    *,
    symbols: list[str] | None = None,
    venues: list[str] | None = None,
    min_discrepancy_pct: float = 0.5,
) -> dict[str, Any]:
    target_symbols = symbols or ["BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "LINK/USD"]
    target_venues = venues or ["coinbase", "kraken"]

    exchanges: dict[str, Any] = {}
    try:
        for venue in target_venues:
            ex_cls = getattr(ccxt, venue, None)
            if ex_cls is None:
                continue
            exchanges[venue] = ex_cls({"enableRateLimit": True})

        rows: list[dict[str, Any]] = []

        for symbol in target_symbols:
            quotes: list[dict[str, Any]] = []
            for venue, ex in exchanges.items():
                try:
                    ticker = ex.fetch_ticker(symbol)
                    last = _safe_float(ticker.get("last"), 0.0)
                    bid = _safe_float(ticker.get("bid"), 0.0)
                    ask = _safe_float(ticker.get("ask"), 0.0)
                    px = last or bid or ask
                    if px > 0:
                        quotes.append({
                            "venue": venue,
                            "symbol": symbol,
                            "price": px,
                            "bid": bid,
                            "ask": ask,
                        })
                except Exception:
                    continue

            if len(quotes) < 2:
                continue

            sorted_quotes = sorted(quotes, key=lambda r: r["price"])
            low = sorted_quotes[0]
            high = sorted_quotes[-1]
            discrepancy_pct = ((high["price"] - low["price"]) / low["price"] * 100.0) if low["price"] > 0 else 0.0

            if discrepancy_pct >= float(min_discrepancy_pct):
                rows.append({
                    "symbol": symbol,
                    "buy_venue": low["venue"],
                    "buy_price": round(low["price"], 8),
                    "sell_venue": high["venue"],
                    "sell_price": round(high["price"], 8),
                    "discrepancy_pct": round(discrepancy_pct, 4),
                    "quotes": quotes,
                })

        rows.sort(key=lambda r: r["discrepancy_pct"], reverse=True)

        return {
            "ok": True,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rows": rows,
            "scanned_symbols": len(target_symbols),
            "venues": target_venues,
        }
    finally:
        for ex in exchanges.values():
            try:
                ex.close()
            except Exception:
                pass
