from __future__ import annotations
import math
from services.markets.math_utils import decimal_value
from services.markets.models import MarketRules
from services.markets.symbols import canonicalize, coinbase_native

def fetch_rules(canonical_symbol: str, *, strict_precision: bool = False) -> MarketRules:
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
    if strict_precision:
        # Coinbase's installed adapter exposes increments, not decimal counts.
        # Unknown modes are not guessed into trading-size metadata.
        if type(strict_precision) is not bool or ex.precisionMode != ccxt.TICK_SIZE:
            return MarketRules("coinbase", cs, coinbase_native(cs), False,
                               meta={"error": "UNSUPPORTED_PRECISION_MODE"})
        def increment(value):
            if isinstance(value, bool):
                raise ValueError("invalid_increment")
            exact = decimal_value(value, name="increment")
            result = float(exact)
            if not math.isfinite(result) or result <= 0 or decimal_value(str(result)) != exact:
                raise ValueError("invalid_increment")
            return result
        try:
            qty_step = increment(prec.get("amount"))
            price_tick = increment(prec.get("price"))
            info = m.get("info") or {}
            native_price_step = info.get("price_increment")
            if native_price_step is None:
                native_price_step = info.get("quote_increment")
            if (qty_step != increment(info.get("base_increment"))
                    or price_tick != increment(native_price_step)):
                raise ValueError("increment_identity")
        except (TypeError, ValueError, OverflowError):
            return MarketRules("coinbase", cs, coinbase_native(cs), False,
                               meta={"error": "INVALID_PRODUCT_INCREMENT"})
    try:
        amt_prec = prec.get("amount")
        if amt_prec is not None and not strict_precision:
            ap = float(amt_prec)
            if ap >= 1 and ap.is_integer():
                qty_step = 10.0 ** (-int(ap))
            elif 0 < ap < 1:
                qty_step = ap
    except Exception:
        pass
    try:
        price_prec = prec.get("price")
        if price_prec is not None and not strict_precision:
            pp = float(price_prec)
            if pp >= 1 and pp.is_integer():
                price_tick = 10.0 ** (-int(pp))
            elif 0 < pp < 1:
                price_tick = pp
    except Exception:
        pass

    info = m.get("info") if isinstance(m.get("info"), dict) else {}
    product = {key: info.get(key) for key in
               ("status", "trading_disabled", "cancel_only", "limit_only", "post_only", "auction_mode")}
    product["product_id"] = info.get("product_id") or info.get("id")
    if "view_only" in info:
        product["view_only"] = info["view_only"]
    return MarketRules("coinbase", cs, str(m.get("id") or coinbase_native(cs)), bool(active), min_notional=min_notional, min_qty=min_qty, qty_step=qty_step, price_tick=price_tick, meta={"ccxt_symbol": ccxt_symbol, "coinbase_product": product})
