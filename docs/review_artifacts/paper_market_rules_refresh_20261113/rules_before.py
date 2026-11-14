from __future__ import annotations
import os
import math
from typing import Optional
from services.markets.models import MarketRules, ValidationResult
from services.markets.symbols import canonicalize
from services.markets.math_utils import decimal_step_ok, decimal_value
from services.markets.cache_sqlite import get as cache_get, upsert as cache_upsert, is_fresh, any_fresh, default_exec_db

DEFAULT_TTL_S = 6 * 3600.0

def fetch_and_cache(exec_db: str, venue: str, canonical_symbol: str) -> MarketRules:
    v = venue.lower().strip()
    cs = canonicalize(canonical_symbol)

    # best-effort native symbol for error cases
    native = cs
    try:
        from services.markets.symbols import binance_native, gate_native, coinbase_native
        if v == "binance":
            native = binance_native(cs)
        elif v == "gate":
            native = gate_native(cs)
        elif v in ("coinbase", "coinbase_adv"):
            native = coinbase_native(cs)
    except Exception:
        pass

    try:
        if v == "binance":
            from services.markets.fetch_binance import fetch_rules
            r = fetch_rules(cs)
        elif v == "gate":
            from services.markets.fetch_gate import fetch_rules
            r = fetch_rules(cs)
        elif v in ("coinbase", "coinbase_adv"):
            from services.markets.fetch_coinbase_ccxt import fetch_rules
            r = fetch_rules(cs)
        else:
            r = MarketRules(v, cs, native, False, meta={"error":"UNSUPPORTED_VENUE"})
    except Exception as e:
        r = MarketRules(v, cs, native, False, meta={"error":"FETCH_FAILED", "detail": f"{type(e).__name__}:{e}"})

    cache_upsert(exec_db, r)
    return r


def get_rules(exec_db: str, venue: str, canonical_symbol: str, ttl_s: float = DEFAULT_TTL_S, refresh_if_stale: bool = True) -> Optional[MarketRules]:
    v = venue.lower().strip()
    cs = canonicalize(canonical_symbol)
    if is_fresh(exec_db, v, cs, ttl_s):
        return cache_get(exec_db, v, cs)
    if refresh_if_stale:
        return fetch_and_cache(exec_db, v, cs)
    return cache_get(exec_db, v, cs)


def _invalid_result(
    code: str,
    message: str,
    rules: Optional[MarketRules],
    **meta: object,
) -> ValidationResult:
    return ValidationResult(False, code, message, rules, dict(meta))


def _coinbase_mode_code(rules: MarketRules, order_type: str) -> str | None:
    meta = rules.meta if isinstance(rules.meta, dict) else {}
    product = meta.get("coinbase_product")
    if (not isinstance(product, dict) or product.get("product_id") != rules.native_symbol
            or type(product.get("status")) is not str or not product["status"]
            or any(type(product.get(flag)) is not bool for flag in
                   ("trading_disabled", "cancel_only", "limit_only", "post_only", "auction_mode"))
            or ("view_only" in product and type(product["view_only"]) is not bool)):
        return "COINBASE_PRODUCT_MODE_UNKNOWN"
    if order_type not in ("market", "limit"):
        return "COINBASE_ORDER_TYPE_UNSUPPORTED"
    if product["status"] != "online" or product["trading_disabled"] or product.get("view_only", False):
        return "COINBASE_PRODUCT_UNAVAILABLE"
    if product["cancel_only"]:
        return "COINBASE_CANCEL_ONLY"
    if product["post_only"] or product["auction_mode"]:
        return "COINBASE_RESTRICTED_MODE_UNSUPPORTED"
    if product["limit_only"] and order_type != "limit":
        return "COINBASE_LIMIT_ONLY"
    return None


def validate(exec_db: str, venue: str, canonical_symbol: str, qty: Optional[float] = None, notional: Optional[float] = None, ttl_s: float = DEFAULT_TTL_S, *, order_type: str | None = None) -> ValidationResult:
    v = venue.lower().strip()
    cs = canonicalize(canonical_symbol)
    check_modes = v in ("coinbase", "coinbase_adv") and order_type is not None
    if check_modes and (isinstance(ttl_s, bool) or not isinstance(ttl_s, (int, float))
                        or not math.isfinite(ttl_s) or ttl_s <= 0):
        return ValidationResult(False, "INVALID_MARKET_RULES_TTL", "Positive finite cache TTL required", None, {})
    r = get_rules(exec_db, v, cs, ttl_s=ttl_s, refresh_if_stale=True)
    if not r:
        return ValidationResult(False, "MARKET_RULES_MISSING", "Market rules missing (cache empty and refresh failed)", None, {"venue": v, "symbol": cs})
    if not r.active:
        return ValidationResult(False, "MARKET_INACTIVE", "Market not active/tradable", r, {})
    if check_modes:
        # Upgrade a legacy cache entry through the existing public fetch path.
        if r.meta is None or (isinstance(r.meta, dict) and "coinbase_product" not in r.meta):
            r = fetch_and_cache(exec_db, v, cs)
            if not r or not r.active:
                return ValidationResult(False, "MARKET_INACTIVE", "Market refresh unavailable or inactive", r, {})
        mode_code = _coinbase_mode_code(r, order_type)
        if mode_code:
            return ValidationResult(False, mode_code, "Coinbase product mode blocks this order type", r, {})
    if notional is not None and r.min_notional is not None:
        try:
            notional_d = decimal_value(notional, name="notional")
        except ValueError as exc:
            return _invalid_result("INVALID_NOTIONAL", str(exc), r, notional=str(notional))
        try:
            min_notional_d = decimal_value(r.min_notional, name="min_notional")
        except ValueError as exc:
            return _invalid_result("INVALID_MARKET_RULES", str(exc), r, field="min_notional")
        if notional_d < min_notional_d:
            return ValidationResult(
                False,
                "MIN_NOTIONAL",
                "Notional below venue minimum",
                r,
                {"notional": float(notional_d), "min_notional": float(min_notional_d)},
            )
    if qty is not None:
        try:
            qty_d = decimal_value(qty, name="qty")
        except ValueError as exc:
            return _invalid_result("INVALID_QTY", str(exc), r, qty=str(qty))
        if r.min_qty is not None:
            try:
                min_qty_d = decimal_value(r.min_qty, name="min_qty")
            except ValueError as exc:
                return _invalid_result("INVALID_MARKET_RULES", str(exc), r, field="min_qty")
            if qty_d < min_qty_d:
                return ValidationResult(
                    False,
                    "MIN_QTY",
                    "Qty below venue minimum",
                    r,
                    {"qty": float(qty_d), "min_qty": float(min_qty_d)},
                )
        if r.qty_step is not None:
            try:
                step_ok = decimal_step_ok(qty_d, r.qty_step)
                step_d = decimal_value(r.qty_step, name="qty_step")
            except ValueError as exc:
                return _invalid_result("INVALID_MARKET_RULES", str(exc), r, field="qty_step")
            if not step_ok:
                return ValidationResult(
                    False,
                    "QTY_STEP",
                    "Qty violates step size",
                    r,
                    {"qty": float(qty_d), "step": float(step_d)},
                )
    return ValidationResult(True, "OK", "Market rules validated", r, {})

def cache_any_fresh(exec_db: str, ttl_s: float = DEFAULT_TTL_S) -> bool:
    return any_fresh(exec_db, ttl_s)
