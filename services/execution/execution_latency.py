from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from storage.market_ws_store_sqlite import SQLiteMarketWsStore


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class ExecutionLatencyTracker:
    store: SQLiteMarketWsStore
    # client_order_id -> timestamps
    submit_ts: Dict[str, int] = field(default_factory=dict)
    ack_ts: Dict[str, int] = field(default_factory=dict)

    def record_measurement(
        self,
        *,
        name: str,
        value_ms: float,
        meta: Dict[str, Any] | None = None,
        category: str = "execution",
    ) -> None:
        self.store.log_latency(
            ts_ms=now_ms(),
            category=str(category),
            name=str(name),
            value_ms=max(0.0, float(value_ms)),
            meta=meta or {},
        )

    def record_submit(self, *, client_order_id: str, exchange: str, symbol: str, side: str, qty: float) -> None:
        ts = now_ms()
        self.submit_ts[client_order_id] = ts
        self.store.log_latency(
            ts_ms=ts,
            category="execution",
            name="order_submit_ms",
            value_ms=0,
            meta={"exchange": exchange, "symbol": symbol, "side": side, "qty": qty, "client_order_id": client_order_id},
        )

    def record_ack(self, *, client_order_id: str, exchange: str, symbol: str, exchange_order_id: str | None = None) -> None:
        ts = now_ms()
        self.ack_ts[client_order_id] = ts
        sub = self.submit_ts.get(client_order_id)
        ack_ms = int(ts - sub) if sub is not None else 0
        self.store.log_latency(
            ts_ms=ts,
            category="execution",
            name="submit_to_ack_ms",
            value_ms=max(0, ack_ms),
            meta={"exchange": exchange, "symbol": symbol, "client_order_id": client_order_id, "exchange_order_id": exchange_order_id},
        )

    def record_fill(self, *, client_order_id: str, exchange: str, symbol: str, price: float | None, qty: float | None) -> None:
        ts = now_ms()
        ack = self.ack_ts.get(client_order_id)
        fill_ms = int(ts - ack) if ack is not None else 0
        self.store.log_latency(
            ts_ms=ts,
            category="execution",
            name="ack_to_fill_ms",
            value_ms=max(0, fill_ms),
            meta={"exchange": exchange, "symbol": symbol, "client_order_id": client_order_id, "price": price, "qty": qty},
        )
