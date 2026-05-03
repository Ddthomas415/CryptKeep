"""Paper adapter for supervised execution path."""

from __future__ import annotations

from typing import Any

from services.execution.paper_engine import PaperEngine


def _to_adapter_order(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    return {
        "id": str(row.get("order_id") or ""),
        "clientOrderId": str(row.get("client_order_id") or ""),
        "status": str(row.get("status") or "new"),
        "symbol": str(row.get("symbol") or ""),
        "side": str(row.get("side") or ""),
        "amount": float(row.get("qty") or 0.0),
        "price": row.get("limit_price"),
        "type": str(row.get("order_type") or "market"),
        "_paper": True,
    }


class PaperEngineAdapter:
    def __init__(self, venue: str) -> None:
        self._venue = str(venue).lower().strip()
        self._engine = PaperEngine()

    def find_order_by_client_oid(self, symbol: str, client_oid: str) -> dict[str, Any] | None:
        return _to_adapter_order(self._engine.db.get_order_by_client_id(str(client_oid)))

    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float | None = None,
        order_type: str = "market",
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        result = self._engine.submit_order(
            client_order_id=str(client_oid or ""),
            venue=self._venue,
            symbol=str(symbol),
            side=str(side),
            order_type=str(order_type),
            qty=float(qty),
            limit_price=float(price) if price is not None else None,
        )
        if not result.get("ok"):
            return result

        order = result.get("order") or {}
        return {
            "ok": True,
            "id": str(order.get("order_id") or ""),
            "clientOrderId": str(order.get("client_order_id") or client_oid or ""),
            "status": str(order.get("status") or "new"),
            "_paper": True,
        }

    def fetch_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        rows = self._engine.db.list_orders(limit=500, status="new")
        if symbol:
            sym = str(symbol).strip().upper()
            rows = [r for r in rows if str(r.get("symbol") or "").strip().upper() == sym]
        return [o for o in (_to_adapter_order(r) for r in rows) if o]

    def fetch_order(self, symbol: str, order_id: str) -> dict[str, Any] | None:
        return _to_adapter_order(self._engine.db.get_order_by_order_id(str(order_id)))
