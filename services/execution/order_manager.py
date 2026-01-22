from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, Optional

from services.execution.normalize_ccxt import normalize_order
from services.execution.place_order import place_order_async

from services.execution.event_log import log_event
from services.execution.event_hooks import (
    log_cancel_requested, log_cancel_result,
    log_replace_requested, log_replace_result,
)
from storage.order_manager_store_sqlite import OrderManagerStoreSQLite

def _idem_default(venue: str, symbol: str, side: str, qty: float, price: float, bucket_sec: int = 5) -> str:
    b = int(time.time() // int(bucket_sec))
    raw = f"{venue}|{symbol}|{side}|{qty:.10f}|{price:.10f}|b{b}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class OrderManager:
    def __init__(self) -> None:
        self.store = OrderManagerStoreSQLite()

    async def submit_limit(
        self, ex, venue: str, symbol: str, side: str, qty: float, price: float, idem_key: Optional[str] = None, params: Optional[dict] = None
    ) -> dict:
        venue = str(venue)
        symbol = str(symbol)
        side = str(side).lower()
        qty = float(qty)
        price = float(price)
        idem_key = idem_key or _idem_default(venue, symbol, side, qty, price)
        params = params or {}

        hit = self.store.idem_get(idem_key)
        if hit and hit.get("order_id"):
            oid = str(hit["order_id"])
            log_event(venue, symbol, "order_submit_idempotent_replay", ref_id=oid, payload={"idem_key": idem_key})
            return {"id": oid, "idempotent_replay": True, "idem_key": idem_key}

        o = await place_order_async(ex, symbol, "limit", side, qty, price, params)
        no = normalize_order(o)
        oid = str(no.get("id") or "")
        self.store.idem_set(idem_key, venue, symbol, side, qty, price, oid or None)

        if oid:
            self.store.upsert_order_snapshot(venue, symbol, oid, {
                "status": no.get("status"),
                "side": side,
                "qty": qty,
                "price": price,
                "filled": no.get("filled"),
                "average": no.get("average"),
                "timestamp": no.get("timestamp"),
            })
            log_event(venue, symbol, "order_submitted", ref_id=oid, payload={"side": side, "qty": qty, "price": price, "idem_key": idem_key, "source": "OrderManager.submit_limit"})
        return o