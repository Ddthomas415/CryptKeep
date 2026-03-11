from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict

from services.execution.paper_engine import PaperEngine


@dataclass(frozen=True)
class PaperOrder:
    venue: str
    symbol: str
    side: str
    order_type: str
    qty: float
    limit_price: float | None = None
    client_order_id: str | None = None


class PaperBroker:
    def __init__(self, engine: PaperEngine | None = None) -> None:
        self.engine = engine or PaperEngine()

    def submit(self, order: PaperOrder) -> Dict[str, Any]:
        cid = str(order.client_order_id or f"paper-{uuid.uuid4().hex[:12]}")
        return self.engine.submit_order(
            client_order_id=cid,
            venue=str(order.venue),
            symbol=str(order.symbol),
            side=str(order.side),
            order_type=str(order.order_type),
            qty=float(order.qty),
            limit_price=(None if order.limit_price is None else float(order.limit_price)),
        )

    def cancel(self, client_order_id: str) -> Dict[str, Any]:
        return self.engine.cancel_order(str(client_order_id))

    def evaluate(self) -> Dict[str, Any]:
        return self.engine.evaluate_open_orders()

    def mtm(self, venue: str, symbol: str) -> Dict[str, Any]:
        return self.engine.mark_to_market(venue=str(venue), symbol=str(symbol))
