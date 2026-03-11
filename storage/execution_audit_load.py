from __future__ import annotations

from typing import Any, Dict

from storage.execution_audit_reader import list_fills, list_orders, list_statuses


def load_orders(*, limit: int = 500, venue: str | None = None, symbol: str | None = None, status: str | None = None) -> Dict[str, Any]:
    rows = list_orders(limit=int(limit), venue=venue, symbol=symbol, status=status)
    return {"ok": True, "count": len(rows), "rows": rows}


def load_fills(
    *,
    limit: int = 500,
    venue: str | None = None,
    symbol: str | None = None,
    exchange_order_id: str | None = None,
) -> Dict[str, Any]:
    rows = list_fills(limit=int(limit), venue=venue, symbol=symbol, exchange_order_id=exchange_order_id)
    return {"ok": True, "count": len(rows), "rows": rows}


def load_all(
    *,
    order_limit: int = 500,
    fill_limit: int = 500,
    venue: str | None = None,
    symbol: str | None = None,
) -> Dict[str, Any]:
    orders = list_orders(limit=int(order_limit), venue=venue, symbol=symbol, status=None)
    fills = list_fills(limit=int(fill_limit), venue=venue, symbol=symbol, exchange_order_id=None)
    statuses = list_statuses()
    return {
        "ok": True,
        "orders_count": len(orders),
        "fills_count": len(fills),
        "statuses": statuses,
        "orders": orders,
        "fills": fills,
    }
