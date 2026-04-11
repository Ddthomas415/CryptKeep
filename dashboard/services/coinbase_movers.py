from __future__ import annotations

import math
import time
from typing import Any

import ccxt


QUOTE_SUFFIXES = ("/USD", "/USDC")
EXCLUDED_BASES = {"USD", "USDC", "EUR", "GBP"}


def _safe(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def _is_spot_usd_symbol(sym: str) -> bool:
    if not isinstance(sym, str) or "/" not in sym:
        return False
    if not sym.endswith(QUOTE_SUFFIXES):
        return False
    base = sym.split("/", 1)[0].strip().upper()
    if not base or base in EXCLUDED_BASES:
        return False
    return True


def fetch_coinbase_movers(*, limit: int = 25) -> dict[str, Any]:
    ex = None
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    try:
        ex = ccxt.coinbase({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })

        markets = ex.load_markets()
        symbols = [
            sym for sym, meta in markets.items()
            if _is_spot_usd_symbol(sym)
            and bool((meta or {}).get("active", True))
            and str((meta or {}).get("type") or "spot") == "spot"
        ]

        tickers = ex.fetch_tickers(symbols)

        for sym in symbols:
            try:
                t = tickers.get(sym) or {}
                last = _safe(t.get("last"), 0.0)
                pct = _safe(t.get("percentage"), 0.0)
                base_vol = _safe(t.get("baseVolume"), 0.0)
                quote_vol = _safe(t.get("quoteVolume"), 0.0)
                high = _safe(t.get("high"), 0.0)
                low = _safe(t.get("low"), 0.0)
                bid = _safe(t.get("bid"), 0.0)
                ask = _safe(t.get("ask"), 0.0)

                if last <= 0:
                    continue

                spread_pct = ((ask - bid) / last * 100.0) if bid > 0 and ask > 0 else 0.0
                volatility_pct = ((high - low) / last * 100.0) if high > 0 and low > 0 else 0.0

                results.append({
                    "symbol": sym,
                    "last": round(last, 8),
                    "change_pct": round(pct, 2),
                    "quote_volume_24h": round(quote_vol, 2),
                    "base_volume_24h": round(base_vol, 6),
                    "spread_pct": round(spread_pct, 3),
                    "volatility_pct": round(volatility_pct, 2),
                })
            except Exception as exc:
                errors.append({"symbol": sym, "error": f"{type(exc).__name__}:{exc}"})

    finally:
        try:
            if ex:
                ex.close()
        except Exception:
            pass

    ranked = sorted(
        results,
        key=lambda r: (r["quote_volume_24h"], abs(r["change_pct"])),
        reverse=True,
    )

    gainers = sorted(ranked, key=lambda r: r["change_pct"], reverse=True)[:limit]
    losers = sorted(ranked, key=lambda r: r["change_pct"])[:limit]
    active = sorted(ranked, key=lambda r: r["quote_volume_24h"], reverse=True)[:limit]
    volatile = sorted(ranked, key=lambda r: r["volatility_pct"], reverse=True)[:limit]

    return {
        "ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scanned": len(results),
        "gainers": gainers,
        "losers": losers,
        "most_active": active,
        "most_volatile": volatile,
        "errors": errors,
        "all": ranked,
    }
