from __future__ import annotations
from services.markets.models import MarketRules
from services.markets.symbols import canonicalize, binance_native
from services.markets.http_json import get_json

def fetch_rules(canonical_symbol: str) -> MarketRules:
    cs = canonicalize(canonical_symbol)
    native = binance_native(cs)
    url = f"https://api.binance.com/api/v3/exchangeInfo?symbol={native}"
    data = get_json(url, timeout_s=10.0)
    syms = (data or {}).get("symbols") or []
    if not syms:
        return MarketRules("binance", cs, native, False, meta={"error":"NOT_FOUND"})
    s0 = syms[0]
    status = str(s0.get("status") or "").upper()
    active = (status == "TRADING")

    min_qty = step = min_notional = price_tick = None
    for f in (s0.get("filters") or []):
        ft = f.get("filterType")
        if ft == "LOT_SIZE":
            if f.get("minQty") is not None: min_qty = float(f.get("minQty"))
            if f.get("stepSize") is not None: step = float(f.get("stepSize"))
        elif ft in ("MIN_NOTIONAL","NOTIONAL"):
            if f.get("minNotional") is not None: min_notional = float(f.get("minNotional"))
        elif ft == "PRICE_FILTER":
            if f.get("tickSize") is not None: price_tick = float(f.get("tickSize"))

    return MarketRules("binance", cs, native, bool(active), min_notional=min_notional, min_qty=min_qty, qty_step=step, price_tick=price_tick, meta={"status": status})
