from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

def _now_ms() -> int:
    return int(time.time() * 1000)

def _conn(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    c = sqlite3.connect(path, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c

DDL = """
CREATE TABLE IF NOT EXISTS intents(
  intent_id TEXT PRIMARY KEY,
  ts_ms INTEGER NOT NULL,
  mode TEXT NOT NULL,                 -- paper|live
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,                 -- buy|sell
  order_type TEXT NOT NULL,           -- market|limit
  qty REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL,               -- pending|submitted|filled|canceled|error
  reason TEXT,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_intents_lookup
  ON intents(mode, exchange, symbol, status, ts_ms);

CREATE TABLE IF NOT EXISTS fills(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  intent_id TEXT NOT NULL,
  ts_ms INTEGER NOT NULL,
  price REAL NOT NULL,
  qty REAL NOT NULL,
  fee REAL NOT NULL,
  fee_ccy TEXT NOT NULL,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_fills_intent_ts ON fills(intent_id, ts_ms);
"""

@dataclass
class ExecutionStore:
    path: str = "data/execution.sqlite"

    def __post_init__(self) -> None:
        with _conn(self.path) as c:
            c.executescript(DDL)
            c.commit()

    def list_intents(self, *, mode: str, exchange: str, symbol: str, status: str, limit: int = 200) -> List[Dict[str, Any]]:
        with _conn(self.path) as c:
            rows = c.execute(
                """
                SELECT intent_id, ts_ms, mode, exchange, symbol, side, order_type, qty, limit_price, status, reason, meta_json
                FROM intents
                WHERE mode=? AND exchange=? AND symbol=? AND status=?
                ORDER BY ts_ms DESC
                LIMIT ?
                """,
                (str(mode), str(exchange), str(symbol), str(status), int(limit)),
            ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["meta"] = json.loads(d.get("meta_json") or "{}")
            except Exception:
                d["meta"] = {}
            out.append(d)
        return out

    def set_intent_status(self, *, intent_id: str, status: str, reason: Optional[str] = None) -> None:
        with _conn(self.path) as c:
            c.execute(
                "UPDATE intents SET status=?, reason=? WHERE intent_id=?",
                (str(status), reason, str(intent_id)),
            )
            c.commit()

    def add_fill(self, *, intent_id: str, ts_ms: int, price: float, qty: float, fee: float, fee_ccy: str, meta: Optional[Dict[str, Any]] = None) -> None:
        with _conn(self.path) as c:
            c.execute(
                """
                INSERT INTO fills(intent_id, ts_ms, price, qty, fee, fee_ccy, meta_json)
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    str(intent_id),
                    int(ts_ms),
                    float(price),
                    float(qty),
                    float(fee),
                    str(fee_ccy),
                    json.dumps(meta or {}, default=str)[:200000],
                ),
            )
            c.commit()

    # Optional helper (not required by live_executor, but useful)
    def upsert_intent(self, row: Dict[str, Any]) -> None:
        with _conn(self.path) as c:
            c.execute(
                """
                INSERT INTO intents(intent_id, ts_ms, mode, exchange, symbol, side, order_type, qty, limit_price, status, reason, meta_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(intent_id) DO UPDATE SET
                  ts_ms=excluded.ts_ms,
                  mode=excluded.mode,
                  exchange=excluded.exchange,
                  symbol=excluded.symbol,
                  side=excluded.side,
                  order_type=excluded.order_type,
                  qty=excluded.qty,
                  limit_price=excluded.limit_price,
                  status=excluded.status,
                  reason=excluded.reason,
                  meta_json=excluded.meta_json
                """,
                (
                    str(row["intent_id"]),
                    int(row.get("ts_ms") or _now_ms()),
                    str(row.get("mode") or "paper"),
                    str(row.get("exchange") or ""),
                    str(row.get("symbol") or ""),
                    str(row.get("side") or ""),
                    str(row.get("order_type") or "market"),
                    float(row.get("qty") or 0.0),
                    (None if row.get("limit_price") is None else float(row["limit_price"])),
                    str(row.get("status") or "pending"),
                    (None if row.get("reason") is None else str(row["reason"])),
                    json.dumps(row.get("meta") or {}, default=str)[:200000],
                ),
            )
            c.commit()
