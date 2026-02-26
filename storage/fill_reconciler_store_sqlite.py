from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "fill_reconciler.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS cursors (
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  last_since_ms INTEGER NOT NULL,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (venue, symbol)
);
CREATE TABLE IF NOT EXISTS seen_trades (
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  trade_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  side TEXT,
  qty REAL,
  price REAL,
  fee REAL,
  fee_ccy TEXT,
  PRIMARY KEY (venue, symbol, trade_id)
);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class FillReconcilerStoreSQLite:
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

    def get_since_ms(self, venue: str, symbol: str, default_since_ms: int) -> int:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT last_since_ms FROM cursors WHERE venue=? AND symbol=?",
                (str(venue), str(symbol))
            ).fetchone()
            return int(row[0]) if row else int(default_since_ms)
        finally:
            conn.close()

    def set_since_ms(self, venue: str, symbol: str, since_ms: int) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO cursors(venue, symbol, last_since_ms, updated_ts) VALUES(?,?,?,?) "
                "ON CONFLICT(venue, symbol) DO UPDATE SET last_since_ms=excluded.last_since_ms, updated_ts=excluded.updated_ts",
                (str(venue), str(symbol), int(since_ms), _now()),
            )
        finally:
            conn.close()

    def mark_seen_trade(self, venue: str, symbol: str, trade_id: str, ts: str, side: str, qty: float, price: float, fee: float, fee_ccy: str | None) -> bool:
        conn = self._connect()
        try:
            try:
                conn.execute(
                    "INSERT INTO seen_trades(venue, symbol, trade_id, ts, side, qty, price, fee, fee_ccy) VALUES(?,?,?,?,?,?,?,?,?)",
                    (str(venue), str(symbol), str(trade_id), str(ts), str(side), float(qty), float(price), float(fee), (str(fee_ccy) if fee_ccy else None)),
                )
                return True
            except sqlite3.IntegrityError:
                return False
        finally:
            conn.close()
