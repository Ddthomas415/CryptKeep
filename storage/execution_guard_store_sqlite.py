from __future__ import annotations

import os
import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Optional, Dict, Any
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = Path(os.environ.get("EXEC_GUARD_DB_PATH", str(data_dir() / "execution_guard.sqlite")))

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS day_metrics (
  day TEXT PRIMARY KEY,
  trades INTEGER NOT NULL,
  approx_realized_pnl REAL NOT NULL,
  updated_ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  notional REAL NOT NULL
);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _today() -> str:
    return date.today().isoformat()

class ExecutionGuardStoreSQLite:
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

    async def record_order(self, venue: str, symbol: str, side: str, qty: float, price: float) -> None:
        await asyncio.to_thread(self._record_order_sync, venue, symbol, side, qty, price)

    def _record_order_sync(self, venue: str, symbol: str, side: str, qty: float, price: float) -> None:
        conn = self._connect()
        try:
            day = _today()
            notional = float(qty) * float(price)
            conn.execute(
                "INSERT INTO events(ts, venue, symbol, side, qty, price, notional) VALUES (?,?,?,?,?,?,?)",
                (_now(), str(venue), str(symbol), str(side), float(qty), float(price), float(notional)),
            )
            row = conn.execute("SELECT trades, approx_realized_pnl FROM day_metrics WHERE day=?", (day,)).fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO day_metrics(day, trades, approx_realized_pnl, updated_ts) VALUES (?,?,?,?)",
                    (day, 1, 0.0, _now()),
                )
            else:
                trades, pnl = int(row[0]), float(row[1])
                conn.execute(
                    "UPDATE day_metrics SET trades=?, approx_realized_pnl=?, updated_ts=? WHERE day=?",
                    (trades + 1, pnl, _now(), day),
                )
        finally:
            conn.close()

    async def add_realized_pnl(self, pnl_delta: float) -> None:
        await asyncio.to_thread(self._add_realized_pnl_sync, pnl_delta)

    def _add_realized_pnl_sync(self, pnl_delta: float) -> None:
        conn = self._connect()
        try:
            day = _today()
            row = conn.execute("SELECT trades, approx_realized_pnl FROM day_metrics WHERE day=?", (day,)).fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO day_metrics(day, trades, approx_realized_pnl, updated_ts) VALUES (?,?,?,?)",
                    (day, 0, float(pnl_delta), _now()),
                )
            else:
                trades, pnl = int(row[0]), float(row[1])
                conn.execute(
                    "UPDATE day_metrics SET trades=?, approx_realized_pnl=?, updated_ts=? WHERE day=?",
                    (trades, pnl + float(pnl_delta), _now(), day),
                )
        finally:
            conn.close()

    def get_today_metrics(self) -> Dict[str, Any]:
        conn = self._connect()
        try:
            day = _today()
            row = conn.execute("SELECT trades, approx_realized_pnl, updated_ts FROM day_metrics WHERE day=?", (day,)).fetchone()
            if not row:
                return {"day": day, "trades": 0, "approx_realized_pnl": 0.0, "updated_ts": None}
            return {"day": day, "trades": int(row[0]), "approx_realized_pnl": float(row[1]), "updated_ts": row[2]}
        finally:
            conn.close()


    async def record_trade_attempt(self) -> None:
        await asyncio.to_thread(self._record_trade_attempt_sync)

    def _record_trade_attempt_sync(self) -> None:
        conn = self._connect()
        try:
            day = _today()
            row = conn.execute("SELECT trades, approx_realized_pnl FROM day_metrics WHERE day=?", (day,)).fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO day_metrics(day, trades, approx_realized_pnl, updated_ts) VALUES (?,?,?,?)",
                    (day, 1, 0.0, _now()),
                )
            else:
                trades, pnl = int(row[0]), float(row[1])
                conn.execute(
                    "UPDATE day_metrics SET trades=?, approx_realized_pnl=?, updated_ts=? WHERE day=?",
                    (trades + 1, pnl, _now(), day),
                )
        finally:
            conn.close()
