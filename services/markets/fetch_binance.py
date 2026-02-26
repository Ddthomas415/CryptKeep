from __future__ import annotations

import os
from urllib.error import HTTPError

from services.markets.models import MarketRules
from services.markets.symbols import canonicalize, binance_native
from services.markets.http_json import get_json

# If your network/region blocks api.binance.com (HTTP 451), you can override:
#   export CBP_BINANCE_API_BASE_URL="https://api.binance.us"
def _base_urls() -> list[str]:
    env = (os.environ.get("CBP_BINANCE_API_BASE_URL") or "").strip()
    bases: list[str] = []
    if env:
        bases.append(env.rstrip("/"))
    bases += ["https://api.binance.com", "https://api.binance.us"]
    out: list[str] = []
    for b in bases:
        if b and b not in out:
            out.append(b)
    return out


def fetch_rules(canonical_symbol: str) -> MarketRules:
    cs = canonicalize(canonical_symbol)
    native = binance_native(cs)

    last_err = None
    used_base = None
    data = None

    for base in _base_urls():
        url = f"{base}/api/v3/exchangeInfo?symbol={native}"
        try:
            data = get_json(url, timeout_s=10.0)
            used_base = base
            break
        except HTTPError as e:
            last_err = f"HTTPError:{getattr(e, 'code', 'unknown')}"
        except Exception as e:
            last_err = f"{type(e).__name__}:{e}"

    if not isinstance(data, dict):
        return MarketRules("binance", cs, native, False, meta={"error": "FETCH_FAILED", "detail": last_err, "bases": _base_urls()})

    syms = (data or {}).get("symbols") or []
    if not syms:
        return MarketRules("binance", cs, native, False, meta={"error": "NOT_FOUND", "base": used_base})

    s0 = syms[0]
    status = str(s0.get("status") or "").upper()
    active = (status == "TRADING")

    min_qty = step = min_notional = price_tick = None
    for f in (s0.get("filters") or []):
        ft = f.get("filterType")
        if ft == "LOT_SIZE":
            if f.get("minQty") is not None:
                min_qty = float(f.get("minQty"))
            if f.get("stepSize") is not None:
                step = float(f.get("stepSize"))
        elif ft in ("MIN_NOTIONAL", "NOTIONAL"):
            if f.get("minNotional") is not None:
                min_notional = float(f.get("minNotional"))
        elif ft == "PRICE_FILTER":
            if f.get("tickSize") is not None:
                price_tick = float(f.get("tickSize"))

    return MarketRules(
        "binance",
        cs,
        native,
        bool(active),
        min_notional=min_notional,
        min_qty=min_qty,
        qty_step=step,
        price_tick=price_tick,
        meta={"status": status, "base": used_base},
    )
