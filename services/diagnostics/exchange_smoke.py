from __future__ import annotations

import time
from typing import Any, Dict


def _ok_check(name: str, ok: bool, *, detail: Any = None, error: str | None = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"name": str(name), "ok": bool(ok)}
    if detail is not None:
        out["detail"] = detail
    if error:
        out["error"] = str(error)
    return out


def _build_exchange(exchange_id: str, sandbox: bool):
    from services.execution.exchange_client import ExchangeClient

    return ExchangeClient(exchange_id=str(exchange_id), sandbox=bool(sandbox)).build()


def run_exchange_smoke(
    *,
    exchange_id: str,
    symbol: str,
    sandbox: bool = True,
    include_orderbook: bool = True,
    orderbook_limit: int = 10,
) -> Dict[str, Any]:
    ex_id = str(exchange_id).lower().strip()
    sym = str(symbol).strip()
    started = time.time()
    checks: list[Dict[str, Any]] = []
    ex = None
    try:
        ex = _build_exchange(ex_id, bool(sandbox))
        checks.append(_ok_check("build_exchange", True))
    except Exception as e:
        checks.append(_ok_check("build_exchange", False, error=f"{type(e).__name__}:{e}"))
        return {
            "ok": False,
            "exchange": ex_id,
            "symbol": sym,
            "sandbox": bool(sandbox),
            "checks": checks,
            "elapsed_ms": int((time.time() - started) * 1000),
        }

    try:
        try:
            t = ex.fetch_ticker(sym)
            checks.append(_ok_check("fetch_ticker", isinstance(t, dict), detail={"has_last": bool((t or {}).get("last") is not None)}))
        except Exception as e:
            checks.append(_ok_check("fetch_ticker", False, error=f"{type(e).__name__}:{e}"))

        if include_orderbook:
            try:
                ob = ex.fetch_order_book(sym, limit=int(orderbook_limit))
                bids = (ob or {}).get("bids") if isinstance(ob, dict) else None
                asks = (ob or {}).get("asks") if isinstance(ob, dict) else None
                ok = isinstance(bids, list) and isinstance(asks, list)
                checks.append(_ok_check("fetch_order_book", ok, detail={"bids": len(bids or []), "asks": len(asks or [])}))
            except Exception as e:
                checks.append(_ok_check("fetch_order_book", False, error=f"{type(e).__name__}:{e}"))
    finally:
        try:
            if ex is not None and hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass

    ok = all(bool(c.get("ok")) for c in checks)
    return {
        "ok": bool(ok),
        "exchange": ex_id,
        "symbol": sym,
        "sandbox": bool(sandbox),
        "checks": checks,
        "elapsed_ms": int((time.time() - started) * 1000),
    }
