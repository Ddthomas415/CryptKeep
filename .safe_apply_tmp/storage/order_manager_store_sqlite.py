from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

DB_PATH = Path("data") / "order_manager.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS idempotency (
  idem_key TEXT PRIMARY KEY,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  order_id TEXT,
  created_ts TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  order_id TEXT NOT NULL,
  status TEXT,
  side TEXT,
  qty REAL,
  price REAL,
  filled REAL,
  average REAL,
  timestamp_ms INTEGER,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (venue, symbol, order_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_updated ON orders(updated_ts);
CREATE INDEX IF NOT EXISTS idx_idem_updated ON idempotency(updated_ts);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class OrderManagerStoreSQLite:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db = db_path
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db, isolation_level=None, check_same_thread=False)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _init(self) -> None:
        con = self._connect()
        try:
            for stmt in SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    con.execute(s)
        finally:
            con.close()

    def idem_get(self, idem_key: str) -> Optional[dict]:
        con = self._connect()
        try:
            r = con.execute(
                "SELECT venue, symbol, side, qty, price, order_id, created_ts, updated_ts FROM idempotency WHERE idem_key=?",
                (str(idem_key),)
            ).fetchone()
            if not r:
                return None
            return {"idem_key": idem_key, "venue": r[0], "symbol": r[1], "side": r[2], "qty": r[3], "price": r[4], "order_id": r[5], "created_ts": r[6], "updated_ts": r[7]}
        finally:
            con.close()

    def idem_set(self, idem_key: str, venue: str, symbol: str, side: str, qty: float, price: float, order_id: Optional[str]) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO idempotency(idem_key, venue, symbol, side, qty, price, order_id, created_ts, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(idem_key) DO UPDATE SET order_id=excluded.order_id, updated_ts=excluded.updated_ts",
                (str(idem_key), str(venue), str(symbol), str(side), float(qty), float(price), order_id if order_id else None, _now(), _now())
            )
        finally:
            con.close()

    def upsert_order_snapshot(self, venue: str, symbol: str, order_id: str, snapshot: dict) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO orders(venue, symbol, order_id, status, side, qty, price, filled, average, timestamp_ms, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(venue, symbol, order_id) DO UPDATE SET "
                "status=excluded.status, side=excluded.side, qty=excluded.qty, price=excluded.price, filled=excluded.filled, "
                "average=excluded.average, timestamp_ms=excluded.timestamp_ms, updated_ts=excluded.updated_ts",
                (
                    str(venue), str(symbol), str(order_id),
                    snapshot.get("status"),
                    snapshot.get("side"),
                    float(snapshot.get("qty") or 0.0),
                    float(snapshot.get("price") or 0.0),
                    float(snapshot.get("filled") or 0.0),
                    float(snapshot.get("average") or 0.0),
                    int(snapshot.get("timestamp") or 0) if snapshot.get("timestamp") else None,
                    _now(),
                )
            )
        finally:
            con.close()

    def recent_idem(self, limit: int = 200) -> List[dict]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT idem_key, venue, symbol, side, qty, price, order_id, created_ts, updated_ts FROM idempotency ORDER BY updated_ts DESC LIMIT ?",
                (int(limit),)
            ).fetchall()
            return [{
                "idem_key": r[0], "venue": r[1], "symbol": r[2], "side": r[3], "qty": r[4], "price": r[5],
                "order_id": r[6], "created_ts": r[7], "updated_ts": r[8]
            } for r in rows]
        finally:
            con.close()

    def recent_orders(self, limit: int = 200) -> List[dict]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT venue, symbol, order_id, status, side, qty, price, filled, average, timestamp_ms, updated_ts FROM orders ORDER BY updated_ts DESC LIMIT ?",
                (int(limit),)
            ).fetchall()
            return [{
                "venue": r[0], "symbol": r[1], "order_id": r[2], "status": r[3], "side": r[4],
                "qty": r[5], "price": r[6], "filled": r[7], "average": r[8], "timestamp_ms": r[9], "updated_ts": r[10]
            } for r in rows]
        finally:
            con.close()
