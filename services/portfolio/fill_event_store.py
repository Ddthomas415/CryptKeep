from __future__ import annotations

import uuid
from typing import Any, Dict, List

from storage.trade_history_sqlite import TradeHistorySQLite


class FillEventStore:
    def __init__(self, store: TradeHistorySQLite | None = None) -> None:
        self.store = store or TradeHistorySQLite()

    def record_fill(self, fill: Dict[str, Any]) -> Dict[str, Any]:
        row = dict(fill or {})
        row.setdefault("trade_id", str(row.get("fill_id") or uuid.uuid4()))
        row.setdefault("ts_ms", int(row.get("ts_ms") or 0))
        row.setdefault("ts", str(row.get("ts") or ""))
        self.store.upsert_trade(row)
        return {"ok": True, "trade_id": row["trade_id"]}

    def recent(self, *, limit: int = 200, venue: str | None = None, symbol: str | None = None) -> List[Dict[str, Any]]:
        return self.store.recent(limit=int(limit), venue=venue, symbol=symbol)
