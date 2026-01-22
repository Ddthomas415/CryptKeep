from __future__ import annotations
from services.admin.config_editor import load_user_yaml
from services.security.exchange_factory import make_exchange
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from services.execution.retry_policy import is_retryable_exception, backoff_sleep
from storage.idempotency_sqlite import IdempotencySQLite

def _cfg() -> dict:
    cfg = load_user_yaml()
    lt = cfg.get("live_trading") or {}
    ex = lt.get("execution") or {}
    return {
        "max_order_retries": int(ex.get("max_order_retries",3)),
        "base_retry_delay_sec": float(ex.get("base_retry_delay_sec",0.6)),
        "max_retry_delay_sec": float(ex.get("max_retry_delay_sec",6.0)),
    }

def place_order_idempotent(*, venue, symbol, side, type, amount, price=None, idempotency_key, params=None, dry_run=True) -> dict:
    v = normalize_venue(venue)
    sym = normalize_symbol(symbol)
    side = str(side).lower().strip()
    type = str(type).lower().strip()
    params = params or {}
    idem = IdempotencySQLite()
    prior = idem.get(idempotency_key)
    if prior and prior.get("status") == "success":
        return {"ok": True, "idempotent": True, "result": prior.get("result"), "key": idempotency_key}
    if dry_run:
        result = {
            "dry_run": True, "venue": v, "symbol": sym,
            "side": side, "type": type, "amount": float(amount),
            "price": (float(price) if price else None), "params": params
        }
        idem.put_success(idempotency_key,result)
        return {"ok": True, "dry_run": True, "result": result, "_

