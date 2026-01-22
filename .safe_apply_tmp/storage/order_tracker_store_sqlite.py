from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path("data") / "order_tracker.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS orders (
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  order_id TEXT NOT NULL,
  placed_ts_ms INTEGER NOT NULL,
  side TEXT,
  qty REAL,
  price REAL,
  last_filled REAL NOT NULL DEFAULT 0.0,
  first_fill_ts_ms INTEGER,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (venue, symbol, order_id)
);
CREATE TABLE IF NOT EXISTS fill_lags (
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  order_id TEXT NOT NULL,
  lag_ms INTEGER NOT NULL,
  first_fill_ts_ms INTEGER NOT NULL,
  placed_ts_ms INTEGER NOT NULL,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (venue, symbol, order_id)
);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class OrderTrackerStoreSQLite:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db = db_path
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init(self) -> None:
        conn = self._connect()
        try:
            for stmt in SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    conn.execute(s)
        finally:
            conn.close()

    def upsert_order(self, venue: str, symbol: str, order_id: str, placed_ts_ms: int, side: str, qty: float, price: float) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO orders(venue, symbol, order_id, placed_ts_ms, side, qty, price, last_filled, first_fill_ts_ms, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(venue, symbol, order_id) DO UPDATE SET "
                "placed_ts_ms=excluded.placed_ts_ms, side=excluded.side, qty=excluded.qty, price=excluded.price, updated_ts=excluded.updated_ts",
                (str(venue), str(symbol), str(order_id), int(placed_ts_ms), str(side), float(qty), float(price), 0.0, None, _now()),
            )
        finally:
            conn.close()

    def get_order(self, venue: str, symbol: str, order_id: str) -> Optional[dict]:
        conn = self._connect()
        try:
            r = conn.execute(
                "SELECT placed_ts_ms, side, qty, price, last_filled, first_fill_ts_ms, updated_ts FROM orders WHERE venue=? AND symbol=? AND order_id=?",
                (str(venue), str(symbol), str(order_id)),
            ).fetchone()
            if not r:
                return None
            return {
                "venue": str(venue), "symbol": str(symbol), "order_id": str(order_id),
                "placed_ts_ms": int(r[0]), "side": r[1], "qty": r[2], "price": r[3],
                "last_filled": float(r[4] or 0.0),
                "first_fill_ts_ms": (int(r[5]) if r[5] is not None else None),
                "updated_ts": r[6],
            }
        finally:
            conn.close()

    def list_open_candidates(self, limit: int = 200) -> List[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT venue, symbol, order_id, placed_ts_ms, side, qty, price, last_filled, first_fill_ts_ms, updated_ts "
                "FROM orders ORDER BY updated_ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            out = []
            for r in rows:
                out.append({
                    "venue": r[0], "symbol": r[1], "order_id": r[2],
                    "placed_ts_ms": int(r[3]), "side": r[4], "qty": r[5], "price": r[6],
                    "last_filled": float(r[7] or 0.0),
                    "first_fill_ts_ms": (int(r[8]) if r[8] is not None else None),
                    "updated_ts": r[9],
                })
            return out
        finally:
            conn.close()

    def update_filled(self, venue: str, symbol: str, order_id: str, filled_total: float, first_fill_ts_ms: int | None) -> float:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT last_filled, placed_ts_ms, first_fill_ts_ms FROM orders WHERE venue=? AND symbol=? AND order_id=?",
                (str(venue), str(symbol), str(order_id)),
            ).fetchone()
            if not cur:
                return 0.0
            last_filled = float(cur[0] or 0.0)
            placed_ts_ms = int(cur[1])
            first_prev = cur[2]
            filled_total = float(filled_total or 0.0)
            delta = max(0.0, filled_total - last_filled)
            first_final = first_prev
            if first_prev is None and filled_total > 0 and first_fill_ts_ms is not None:
                first_final = int(first_fill_ts_ms)
            conn.execute(
                "UPDATE orders SET last_filled=?, first_fill_ts_ms=?, updated_ts=? WHERE venue=? AND symbol=? AND order_id=?",
                (float(filled_total), (int(first_final) if first_final is not None else None), _now(), str(venue), str(symbol), str(order_id)),
            )
            if first_prev is None and first_final is not None:
                lag = int(first_final - placed_ts_ms)
                conn.execute(
                    "INSERT INTO fill_lags(venue, symbol, order_id, lag_ms, first_fill_ts_ms, placed_ts_ms, updated_ts) "
                    "VALUES(?,?,?,?,?,?,?) "
                    "ON CONFLICT(venue, symbol, order_id) DO UPDATE SET lag_ms=excluded.lag_ms, first_fill_ts_ms=excluded.first_fill_ts_ms, placed_ts_ms=excluded.placed_ts_ms, updated_ts=excluded.updated_ts",
                    (str(venue), str(symbol), str(order_id), int(lag), int(first_final), int(placed_ts_ms), _now()),
                )
            return float(delta)
        finally:
            conn.close()

    def last_fill_lags(self, limit: int = 100) -> List[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT venue, symbol, order_id, lag_ms, first_fill_ts_ms, placed_ts_ms, updated_ts "
                "FROM fill_lags ORDER BY updated_ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [{
                "venue": r[0], "symbol": r[1], "order_id": r[2],
                "lag_ms": int(r[3]), "first_fill_ts_ms": int(r[4]), "placed_ts_ms": int(r[5]),
                "updated_ts": r[6],
            } for r in rows]
        finally:
            conn.close()
