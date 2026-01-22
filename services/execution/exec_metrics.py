from __future__ import annotations
from storage.exec_metrics_sqlite import ExecMetricsSQLite

def _safe_float(x) -> float | None:
    try: return None if x is None else float(x)
    except Exception: return None

def compute_slippage_bps(intended_price: float | None, fill_price: float | None) -> float | None:
    ip, fp = _safe_float(intended_price), _safe_float(fill_price)
    if ip is None or fp is None or ip == 0: return None
    return abs((fp - ip)/ip) * 10000.0

def record_exec_metric(*, decision_id: str | None, intent_id: str | None, venue: str, symbol: str,
                       side: str, qty: float, intended_price: float | None, ack_ms: float | None,
                       fill_price: float | None, exchange_order_id: str | None, status: str | None):
    store = ExecMetricsSQLite()
    store.insert(
        decision_id=decision_id, intent_id=intent_id, venue=venue, symbol=symbol, side=side,
        qty=float(qty), intended_price=_safe_float(intended_price), ack_ms=_safe_float(ack_ms),
        fill_price=_safe_float(fill_price), slippage_bps=compute_slippage_bps(intended_price, fill_price),
        exchange_order_id=exchange_order_id, status=status
    )
