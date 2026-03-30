from __future__ import annotations
from services.markets.models import MarketRules
from services.markets.symbols import canonicalize, coinbase_native

def fetch_rules(canonical_symbol: str) -> MarketRules:
    cs = canonicalize(canonical_symbol)
    try:
        import ccxt  # type: ignore
    except Exception:
        return MarketRules("coinbase", cs, coinbase_native(cs), False, meta={"error":"CCXT_NOT_AVAILABLE"})

    ex = getattr(ccxt, "coinbase")({"enableRateLimit": True})
    markets = ex.load_markets()

    ccxt_symbol = cs.replace("-", "/") if "-" in cs else cs
    m = markets.get(ccxt_symbol)
    if not m:
        return MarketRules("coinbase", cs, coinbase_native(cs), False, meta={"error":"NOT_FOUND", "ccxt_symbol": ccxt_symbol})

    active = bool(m.get("active", True))

    min_qty = min_notional = qty_step = price_tick = None
    lim = m.get("limits") or {}
    amt = (lim.get("amount") or {})
    cost = (lim.get("cost") or {})
    try:
        if amt.get("min") is not None: min_qty = float(amt.get("min"))
    except Exception:
        pass
    try:
        if cost.get("min") is not None: min_notional = float(cost.get("min"))
    except Exception:
        pass

    prec = m.get("precision") or {}
    try:
        amt_prec = prec.get("amount")
        if amt_prec is not None:
            ap = float(amt_prec)
            if ap >= 1 and ap.is_integer():
                qty_step = 10.0 ** (-int(ap))
            elif 0 < ap < 1:
                qty_step = ap
    except Exception:
        pass
    try:
        price_prec = prec.get("price")
        if price_prec is not None:
            pp = float(price_prec)
            if pp >= 1 and pp.is_integer():
                price_tick = 10.0 ** (-int(pp))
            elif 0 < pp < 1:
                price_tick = pp
    except Exception:
        pass

    return MarketRules("coinbase", cs, str(m.get("id") or coinbase_native(cs)), bool(active), min_notional=min_notional, min_qty=min_qty, qty_step=qty_step, price_tick=price_tick, meta={"ccxt_symbol": ccxt_symbol})
