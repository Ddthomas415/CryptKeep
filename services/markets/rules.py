from __future__ import annotations
import os
from typing import Optional
from services.markets.models import MarketRules, ValidationResult
from services.markets.symbols import canonicalize
from services.markets.math_utils import step_ok
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

def validate(exec_db: str, venue: str, canonical_symbol: str, qty: Optional[float] = None, notional: Optional[float] = None, ttl_s: float = DEFAULT_TTL_S) -> ValidationResult:
    v = venue.lower().strip()
    cs = canonicalize(canonical_symbol)
    r = get_rules(exec_db, v, cs, ttl_s=ttl_s, refresh_if_stale=True)
    if not r:
        return ValidationResult(False, "MARKET_RULES_MISSING", "Market rules missing (cache empty and refresh failed)", None, {"venue": v, "symbol": cs})
    if not r.active:
        return ValidationResult(False, "MARKET_INACTIVE", "Market not active/tradable", r, {})
    if notional is not None and r.min_notional is not None and float(notional) < float(r.min_notional):
        return ValidationResult(False, "MIN_NOTIONAL", "Notional below venue minimum", r, {"notional": float(notional), "min_notional": float(r.min_notional)})
    if qty is not None:
        if r.min_qty is not None and float(qty) < float(r.min_qty):
            return ValidationResult(False, "MIN_QTY", "Qty below venue minimum", r, {"qty": float(qty), "min_qty": float(r.min_qty)})
        if r.qty_step is not None and not step_ok(float(qty), float(r.qty_step)):
            return ValidationResult(False, "QTY_STEP", "Qty violates step size", r, {"qty": float(qty), "step": float(r.qty_step)})
    return ValidationResult(True, "OK", "Market rules validated", r, {})

def cache_any_fresh(exec_db: str, ttl_s: float = DEFAULT_TTL_S) -> bool:
    return any_fresh(exec_db, ttl_s)
