from __future__ import annotations
import inspect
from services.execution.place_order import place_order as _place_order

_PO_SIG = inspect.signature(_place_order)
_PO_PARAM_NAMES = tuple(_PO_SIG.parameters.keys())

def _place_order_ccxt(ex, symbol, type, side, amount, price, params):
    # Preferred: ccxt-like positional call
    try:
        return _place_order(ex, symbol, type, side, amount, price, params)
    except TypeError:
        # Fallback: map by parameter names (if place_order signature differs)
        kw = {}
        if _PO_PARAM_NAMES:
            kw[_PO_PARAM_NAMES[0]] = ex
        def _set(names, value):
            for n in names:
                if n in _PO_PARAM_NAMES:
                    kw[n] = value
                    return
        _set(("symbol","sym","market","pair"), symbol)
        _set(("type","order_type","otype"), type)
        _set(("side",), side)
        _set(("amount","qty","size","quantity"), amount)
        if price is not None:
            _set(("price","limit_price"), price)
        _set(("params","extra"), params)
        return _place_order(**kw)


import json
import os
from typing import Any, Dict

from services.admin.config_editor import load_user_yaml
from services.execution.retry_policy import backoff_sleep, is_retryable_exception
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from services.security.exchange_factory import make_exchange
from storage.idempotency_sqlite import IdempotencySQLite


def _cfg() -> dict:
    cfg = load_user_yaml()
    lt = cfg.get("live_trading") or {}
    ex = lt.get("execution") or {}
    return {
        "max_order_retries": int(ex.get("max_order_retries", 3)),
        "base_retry_delay_sec": float(ex.get("base_retry_delay_sec", 0.6)),
        "max_retry_delay_sec": float(ex.get("max_retry_delay_sec", 6.0)),
    }


def _creds_from_env(venue: str) -> dict:
    ex = str(venue).upper().replace(".", "_")
    key = os.environ.get(f"{ex}_API_KEY") or os.environ.get("CBP_API_KEY")
    sec = os.environ.get(f"{ex}_API_SECRET") or os.environ.get("CBP_API_SECRET")
    pwd = (
        os.environ.get(f"{ex}_API_PASSPHRASE")
        or os.environ.get(f"{ex}_API_PASSWORD")
        or os.environ.get("CBP_API_PASSPHRASE")
    )
    return {"apiKey": key, "secret": sec, "passphrase": pwd}


def place_order_idempotent(
    *,
    venue: str,
    symbol: str,
    side: str,
    type: str,
    amount: float,
    price: float | None = None,
    idempotency_key: str,
    params: Dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict:
    v = normalize_venue(venue)
    sym = normalize_symbol(symbol)
    side = str(side).lower().strip()
    type = str(type).lower().strip()
    params = params or {}

    idem = IdempotencySQLite()
    prior = idem.get(idempotency_key)
    if prior and prior.get("status") == "success":
        return {
            "ok": True,
            "idempotent": True,
            "result": prior.get("result"),
            "key": idempotency_key,
        }

    if dry_run:
        result = {
            "dry_run": True,
            "venue": v,
            "symbol": sym,
            "side": side,
            "type": type,
            "amount": float(amount),
            "price": (float(price) if price is not None else None),
            "params": params,
        }
        idem.put_success(idempotency_key, result)
        return {"ok": True, "dry_run": True, "result": result, "key": idempotency_key}

    cfg = _cfg()
    max_retries = int(cfg["max_order_retries"])
    base_delay = float(cfg["base_retry_delay_sec"])
    max_delay = float(cfg["max_retry_delay_sec"])

    attempt = 0
    last_err = None
    while True:
        ex = None
        try:
            ex = make_exchange(v, _creds_from_env(v), enable_rate_limit=True)
            result = _place_order_ccxt(ex, sym, type, side, float(amount), float(price) if price is not None else None, params)
            idem.put_success(idempotency_key, result)
            return {"ok": True, "result": result, "key": idempotency_key}
        except Exception as e:
            last_err = f"{type(e).__name__}:{e}"
            if is_retryable_exception(e) and attempt < max_retries:
                attempt += 1
                backoff_sleep(attempt, base_delay, max_delay)
                continue
            idem.put_error(idempotency_key, last_err)
            return {"ok": False, "error": last_err, "key": idempotency_key}
        finally:
            try:
                if ex is not None and hasattr(ex, "close"):
                    ex.close()
            except Exception:
                pass
