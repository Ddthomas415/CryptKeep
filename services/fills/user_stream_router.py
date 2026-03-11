from __future__ import annotations

import hashlib
from typing import Any, Callable, Dict

from services.journal.fill_sink import CanonicalFillSink


def _sym_parts(sym: str) -> tuple[str, str]:
    try:
        if "/" in sym:
            base, quote = str(sym).split("/", 1)
            return (base.strip().upper(), quote.strip().upper())
    except Exception:
        pass
    return ("", "")


def _usd_like(cur: str) -> bool:
    c = str(cur or "").strip().upper()
    return c in {"USD", "USDT", "USDC"}


def _stable_synth_fill_id(exchange_id: str, trade: Dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(exchange_id),
            str(trade.get("timestamp") or ""),
            str(trade.get("order") or trade.get("orderId") or ""),
            str(trade.get("symbol") or ""),
            str(trade.get("side") or ""),
            str(trade.get("amount") or ""),
            str(trade.get("price") or ""),
            str(trade.get("cost") or ""),
        ]
    )
    return "synthetic:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def ccxt_trade_to_fill(exchange_id: str, trade: Dict[str, Any]) -> Dict[str, Any]:
    ex_id = str(exchange_id or "").lower().strip()
    t = dict(trade or {})
    symbol = str(t.get("symbol") or "")
    base, quote = _sym_parts(symbol)

    ts_any = t.get("timestamp") or t.get("datetime") or ""
    ts_str = str(ts_any)

    fill_id = str(t.get("id") or "")
    if not fill_id:
        fill_id = _stable_synth_fill_id(ex_id, t)

    client_order_id = ""
    info = t.get("info") if isinstance(t.get("info"), dict) else {}
    for key in ("clientOrderId", "client_order_id", "newClientOrderId", "text", "clientOid"):
        v = t.get(key) or (info.get(key) if isinstance(info, dict) else None)
        if v:
            client_order_id = str(v)
            break

    fee_usd = 0.0
    fee = t.get("fee")
    try:
        price = float(t.get("price") or 0.0)
    except Exception:
        price = 0.0
    if isinstance(fee, dict):
        try:
            cur = str(fee.get("currency") or "").upper()
            cost = float(fee.get("cost") or 0.0)
            if _usd_like(cur):
                fee_usd = cost
            elif _usd_like(quote) and cur == quote:
                fee_usd = cost
            elif _usd_like(quote) and cur == base and price > 0:
                fee_usd = cost * price
        except Exception:
            fee_usd = 0.0

    return {
        "venue": ex_id,
        "fill_id": fill_id,
        "order_id": str(t.get("order") or t.get("orderId") or ""),
        "client_order_id": client_order_id,
        "symbol": symbol,
        "side": t.get("side") or "",
        "qty": t.get("amount"),
        "price": t.get("price"),
        "ts": ts_str,
        "fee_usd": float(fee_usd),
        "realized_pnl_usd": None,
        "raw": {"ccxt_trade": t},
    }


def _resolve_live_executor_hook() -> Callable[..., Dict[str, Any]] | None:
    try:
        from services.execution import live_executor as _le

        fn = getattr(_le, "_on_fill", None)
        if callable(fn):
            return fn
    except Exception:
        return None
    return None


def route_fill_event(
    fill: Dict[str, Any],
    *,
    exec_db: str,
    prefer_live_executor_hook: bool = True,
    fallback_sink: Any | None = None,
) -> Dict[str, Any]:
    payload = dict(fill or {})
    if prefer_live_executor_hook:
        hook = _resolve_live_executor_hook()
        if callable(hook):
            out = hook(payload, exec_db=str(exec_db))
            if isinstance(out, dict) and bool(out.get("ok")):
                return {"ok": True, "via": "live_executor_hook", "fill_id": payload.get("fill_id"), "result": out}

    sink = fallback_sink if fallback_sink is not None else CanonicalFillSink(exec_db=str(exec_db))
    sink.on_fill(payload)
    return {"ok": True, "via": "fill_sink", "fill_id": payload.get("fill_id")}


def route_ccxt_trade(
    exchange_id: str,
    trade: Dict[str, Any],
    *,
    exec_db: str,
    prefer_live_executor_hook: bool = True,
    fallback_sink: Any | None = None,
) -> Dict[str, Any]:
    fill = ccxt_trade_to_fill(exchange_id, trade)
    if not fill.get("symbol") or not fill.get("side") or fill.get("qty") is None or fill.get("price") is None:
        return {"ok": False, "reason": "invalid_trade_shape", "fill": fill}
    out = route_fill_event(
        fill,
        exec_db=str(exec_db),
        prefer_live_executor_hook=bool(prefer_live_executor_hook),
        fallback_sink=fallback_sink,
    )
    return {"ok": bool(out.get("ok")), "fill": fill, "route": out}

