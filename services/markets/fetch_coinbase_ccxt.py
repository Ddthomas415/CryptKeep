from __future__ import annotations
import math
from services.markets.math_utils import decimal_value
from services.markets.models import MarketRules
from services.markets.symbols import canonicalize, coinbase_native

def fetch_rules(canonical_symbol: str, *, strict_precision: bool = True) -> MarketRules:
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

    info = m.get("info") if isinstance(m.get("info"), dict) else {}
    native = coinbase_native(cs)
    if m.get("id") != native or (info.get("product_id") or info.get("id")) != native:
        return MarketRules("coinbase", cs, native, False, meta={"error": "PRODUCT_IDENTITY_MISMATCH"})

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

    # The keyword remains source-compatible; False cannot restore the old bug.
    mode, tick_mode = getattr(ex, "precisionMode", None), getattr(ccxt, "TICK_SIZE", None)
    if (type(strict_precision) is not bool or type(mode) is not int
            or type(tick_mode) is not int or mode != tick_mode):
        return MarketRules("coinbase", cs, native, False, meta={"error": "UNSUPPORTED_PRECISION_MODE"})

    def increment(value):
        if isinstance(value, bool):
            raise ValueError("invalid_increment")
        exact = decimal_value(value, name="increment")
        result = float(exact)
        if not math.isfinite(result) or result <= 0 or decimal_value(str(result)) != exact:
            raise ValueError("invalid_increment")
        return result

    try:
        prec = m.get("precision")
        if not isinstance(prec, dict):
            raise ValueError("invalid_precision")
        qty_step, price_tick = increment(prec.get("amount")), increment(prec.get("price"))
        native_price_step = info.get("price_increment")
        if native_price_step is None:
            native_price_step = info.get("quote_increment")
        if qty_step != increment(info.get("base_increment")) or price_tick != increment(native_price_step):
            raise ValueError("increment_identity")
    except (TypeError, ValueError, OverflowError):
        return MarketRules("coinbase", cs, native, False, meta={"error": "INVALID_PRODUCT_INCREMENT"})

    info = m.get("info") if isinstance(m.get("info"), dict) else {}
    product = {key: info.get(key) for key in
               ("status", "trading_disabled", "cancel_only", "limit_only", "post_only", "auction_mode")}
    product["product_id"] = info.get("product_id") or info.get("id")
    if "view_only" in info:
        product["view_only"] = info["view_only"]
    return MarketRules("coinbase", cs, str(m.get("id") or coinbase_native(cs)), bool(active), min_notional=min_notional, min_qty=min_qty, qty_step=qty_step, price_tick=price_tick, meta={"ccxt_symbol": ccxt_symbol, "coinbase_product": product})
