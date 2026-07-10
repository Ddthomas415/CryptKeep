from __future__ import annotations

import inspect
import math
from typing import Any, Dict

from services.admin.config_editor import load_user_yaml
from services.execution.place_order import place_order as _place_order
from services.execution.retry_policy import backoff_sleep, is_retryable_exception
from services.execution.execution_context import ExecutionContext
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from services.security.credentials_loader import load_exchange_credentials
from services.security.exchange_factory import make_exchange
from storage.idempotency_sqlite import IdempotencySQLite
from services.execution.order_reconciliation import reconcile_ambiguous_submission

_PO_SIG = inspect.signature(_place_order)
_PO_PARAM_NAMES = tuple(_PO_SIG.parameters.keys())


def _bounded_float(value: Any, *, default: float, lo: float, hi: float) -> float:
    """Parse a retry delay knob into a finite bounded value.

    Config must not be able to hang the submit path with NaN/inf sleeps or
    unbounded exponential backoff.
    """
    try:
        parsed = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return min(float(hi), max(float(lo), parsed))


def _bounded_int(value: Any, *, default: int, lo: int, hi: int) -> int:
    try:
        parsed = float(value)
    except Exception:
        return int(default)
    if not math.isfinite(parsed):
        return int(default)
    return int(min(int(hi), max(int(lo), parsed)))


def _place_order_ccxt(ex, symbol, type, side, amount, price, params, context: ExecutionContext | None = None):
    # Preferred: ccxt-like positional call
    try:
        return _place_order(ex, symbol, type, side, amount, price, params, context=context)
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

        _set(("symbol", "sym", "market", "pair"), symbol)
        _set(("type", "order_type", "otype"), type)
        _set(("side",), side)
        _set(("amount", "qty", "size", "quantity"), amount)
        if price is not None:
            _set(("price", "limit_price"), price)
        _set(("params", "extra"), params)
        if "context" in _PO_PARAM_NAMES:
            kw["context"] = context
        return _place_order(**kw)


def _cfg() -> dict:
    cfg = load_user_yaml()
    lt = cfg.get("live_trading") or {}
    ex = lt.get("execution") or {}
    return {
        "max_order_retries": _bounded_int(
            ex.get("max_order_retries"), default=3, lo=0, hi=10
        ),
        "base_retry_delay_sec": _bounded_float(
            ex.get("base_retry_delay_sec"), default=0.6, lo=0.05, hi=60.0
        ),
        "max_retry_delay_sec": _bounded_float(
            ex.get("max_retry_delay_sec"), default=6.0, lo=0.05, hi=300.0
        ),
    }


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
    context: ExecutionContext | None = None,
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
            creds = load_exchange_credentials(v)
            ex = make_exchange(v, creds, enable_rate_limit=True)
            result = _place_order_ccxt(
                ex,
                sym,
                type,
                side,
                float(amount),
                float(price) if price is not None else None,
                params,
                context=context,
            )
            idem.put_success(idempotency_key, result)
            return {"ok": True, "result": result, "key": idempotency_key}
        except Exception as e:
            last_err = f"{e.__class__.__name__}:{e}"
            if is_retryable_exception(e) and attempt < max_retries:
                recon = reconcile_ambiguous_submission(
                    venue=venue,
                    client=ex,
                    symbol=symbol,
                    client_oid=idempotency_key,
                    remote_order_id=None,
                    age_sec=0,
                )
                if recon.outcome == "confirmed_not_placed":
                    attempt += 1
                    backoff_sleep(attempt, base_delay, max_delay)
                    continue
                raise RuntimeError(f"retry_blocked_after_ambiguous_submit:{recon.outcome}")
            idem.put_error(idempotency_key, last_err)
            return {"ok": False, "error": last_err, "key": idempotency_key}
        finally:
            try:
                if ex is not None and hasattr(ex, "close"):
                    ex.close()
            except Exception as _err:
                pass  # suppressed: order_router.py
