from __future__ import annotations

from typing import Any, Dict, Optional

class OrderParamError(ValueError):
    pass

_ALLOWED = {
    "coinbase": {"clientOrderId", "timeInForce", "postOnly"},
    "binance": {"newClientOrderId", "timeInForce", "postOnly", "recvWindow"},
    "gate": {"text", "timeInForce", "postOnly"},
}

def _norm_ex(exchange_id: str) -> str:
    ex = (exchange_id or "").lower().strip()
    if ex.startswith("coinbase"):
        return "coinbase"
    if ex.startswith("binance"):
        return "binance"
    if ex.startswith("gate"):
        return "gate"
    return ex

def prepare_ccxt_params(*, exchange_id: str, client_order_id: str, order_type: str, price: Optional[float], params: Dict[str, Any], allow_extra: bool=False) -> Dict[str, Any]:
    ex = _norm_ex(exchange_id)
    out: Dict[str, Any] = dict(params or {})

    # normalize
    if "timeInForce" in out and isinstance(out["timeInForce"], str):
        out["timeInForce"] = out["timeInForce"].upper().strip()
    if "postOnly" in out:
        out["postOnly"] = bool(out["postOnly"])

    # enforce postOnly usage
    if out.get("postOnly"):
        if str(order_type).lower().strip() not in ("limit", "limit_maker"):
            raise OrderParamError("postOnly requires a LIMIT order")
        if price is None:
            raise OrderParamError("postOnly requires price")

    # inject venue-specific idempotency key
    if ex == "binance":
        out["newClientOrderId"] = str(client_order_id)
    elif ex == "gate":
        out["text"] = str(client_order_id)
    else:
        out["clientOrderId"] = str(client_order_id)

    allowed = _ALLOWED.get(ex)
    if allowed and not allow_extra:
        out = {k: v for k, v in out.items() if k in allowed}

    tif = out.get("timeInForce")
    if tif and str(tif) not in ("GTC", "IOC", "FOK"):
        raise OrderParamError(f"unsupported timeInForce={tif}")

    return out
