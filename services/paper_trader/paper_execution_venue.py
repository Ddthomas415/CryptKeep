from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

from core.models import Fill, Order, OrderAck, OrderStatus, PortfolioState, Side, utc_now


def _bps_mult(bps: float) -> float:
    return float(bps or 0.0) / 10_000.0


@dataclass
class PaperExecutionVenue:
    venue: str = "paper"
    fee_bps: float = 1.0
    slippage_bps: float = 0.0
    _prices: dict[str, float] = field(default_factory=dict)
    _queue: asyncio.Queue[Fill | None] = field(default_factory=asyncio.Queue)
    _closed: bool = False

    async def connect(self) -> None:
        self._closed = False

    def set_price_for(self, symbol: str, price: float) -> None:
        self._prices[str(symbol)] = float(price)

    async def place_order(self, order: Order) -> OrderAck:
        px = self._prices.get(str(order.symbol))
        if px is None and order.limit_price is not None:
            px = float(order.limit_price)
        if px is None:
            return OrderAck(
                client_order_id=order.client_order_id,
                venue_order_id=None,
                status=OrderStatus.REJECTED,
                message="missing_price",
                ts=utc_now(),
            )

        slip = _bps_mult(self.slippage_bps)
        if order.side == Side.BUY:
            fill_px = float(px) * (1.0 + slip)
        else:
            fill_px = float(px) * (1.0 - slip)
        fee = abs(float(order.qty) * fill_px) * _bps_mult(self.fee_bps)
        venue_order_id = f"paper-{uuid.uuid4().hex[:12]}"
        fill = Fill(
            venue=self.venue,
            symbol=order.symbol,
            side=order.side,
            qty=float(order.qty),
            price=float(fill_px),
            fee=float(fee),
            client_order_id=order.client_order_id,
            venue_order_id=venue_order_id,
            fill_id=f"fill-{uuid.uuid4().hex[:12]}",
            ts=utc_now(),
        )
        await self._queue.put(fill)
        return OrderAck(
            client_order_id=order.client_order_id,
            venue_order_id=venue_order_id,
            status=OrderStatus.FILLED,
            message="filled",
            ts=utc_now(),
        )

    async def cancel_order(self, client_order_id: str) -> bool:
        return False

    async def fills(self):
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item

    async def sync_portfolio(self) -> PortfolioState:
        return PortfolioState()

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.put(None)
