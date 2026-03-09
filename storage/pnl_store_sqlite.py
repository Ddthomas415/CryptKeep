from __future__ import annotations
import asyncio
import sqlite3
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "pnl.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS fills (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL NOT NULL DEFAULT 0.0,
  fee_ccy TEXT
);
CREATE TABLE IF NOT EXISTS positions (
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  qty REAL NOT NULL,
  avg_price REAL NOT NULL,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY(venue, symbol)
);
CREATE TABLE IF NOT EXISTS realized_day (
  day TEXT PRIMARY KEY,
  realized_pnl REAL NOT NULL,
  updated_ts TEXT NOT NULL
);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _today() -> str:
    return date.today().isoformat()

class PnLStoreSQLite:
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

    async def record_fill(self, venue: str, symbol: str, side: str, qty: float, price: float, fee: float = 0.0, fee_ccy: str | None = None) -> Dict[str, Any]:
        return await asyncio.to_thread(self._record_fill_sync, venue, symbol, side, qty, price, fee, fee_ccy)

    def _record_fill_sync(self, venue: str, symbol: str, side: str, qty: float, price: float, fee: float = 0.0, fee_ccy: str | None = None) -> Dict[str, Any]:
        venue = str(venue)
        symbol = str(symbol)
        side = str(side).lower()
        q = float(qty)
        px = float(price)
        fee = float(fee or 0.0)
        if q <= 0 or px <= 0 or side not in ("buy","sell"):
            return {"ok": False, "reason": "bad_fill"}
        conn = self._connect()
        realized_delta = 0.0
        try:
            conn.execute(
                "INSERT INTO fills(ts, venue, symbol, side, qty, price, fee, fee_ccy) VALUES(?,?,?,?,?,?,?,?)",
                (_now(), venue, symbol, side, q, px, fee, (str(fee_ccy) if fee_ccy else None)),
            )
            row = conn.execute(
                "SELECT qty, avg_price FROM positions WHERE venue=? AND symbol=?",
                (venue, symbol)
            ).fetchone()
            pos_qty = float(row[0]) if row else 0.0
            pos_avg = float(row[1]) if row else 0.0
            t_qty = q if side == "buy" else -q
            if pos_qty == 0.0 or (pos_qty > 0 and t_qty > 0) or (pos_qty < 0 and t_qty < 0):
                new_qty = pos_qty + t_qty
                if pos_qty == 0.0:
                    new_avg = px
                else:
                    new_avg = (pos_avg * abs(pos_qty) + px * abs(t_qty)) / max(1e-12, (abs(pos_qty) + abs(t_qty)))
                conn.execute(
                    "INSERT INTO positions(venue, symbol, qty, avg_price, updated_ts) VALUES(?,?,?,?,?) "
                    "ON CONFLICT(venue, symbol) DO UPDATE SET qty=excluded.qty, avg_price=excluded.avg_price, updated_ts=excluded.updated_ts",
                    (venue, symbol, float(new_qty), float(new_avg), _now()),
                )
            else:
                close_qty = min(abs(t_qty), abs(pos_qty))
                if pos_qty > 0 and t_qty < 0:
                    realized_delta += (px - pos_avg) * close_qty
                elif pos_qty < 0 and t_qty > 0:
                    realized_delta += (pos_avg - px) * close_qty
                remaining_qty = pos_qty + t_qty
                if remaining_qty == 0.0:
                    conn.execute(
                        "INSERT INTO positions(venue, symbol, qty, avg_price, updated_ts) VALUES(?,?,?,?,?) "
                        "ON CONFLICT(venue, symbol) DO UPDATE SET qty=excluded.qty, avg_price=excluded.avg_price, updated_ts=excluded.updated_ts",
                        (venue, symbol, 0.0, 0.0, _now()),
                    )
                else:
                    if (pos_qty > 0 and remaining_qty < 0) or (pos_qty < 0 and remaining_qty > 0):
                        new_avg = px
                    else:
                        new_avg = pos_avg
                    conn.execute(
                        "INSERT INTO positions(venue, symbol, qty, avg_price, updated_ts) VALUES(?,?,?,?,?) "
                        "ON CONFLICT(venue, symbol) DO UPDATE SET qty=excluded.qty, avg_price=excluded.avg_price, updated_ts=excluded.updated_ts",
                        (venue, symbol, float(remaining_qty), float(new_avg), _now()),
                    )
            if fee:
                realized_delta -= fee
            if realized_delta != 0.0:
                day = _today()
                r = conn.execute("SELECT realized_pnl FROM realized_day WHERE day=?", (day,)).fetchone()
                cur = float(r[0]) if r else 0.0
                nxt = cur + float(realized_delta)
                conn.execute(
                    "INSERT INTO realized_day(day, realized_pnl, updated_ts) VALUES(?,?,?) "
                    "ON CONFLICT(day) DO UPDATE SET realized_pnl=excluded.realized_pnl, updated_ts=excluded.updated_ts",
                    (day, float(nxt), _now()),
                )
            return {"ok": True, "realized_delta": float(realized_delta)}
        finally:
            conn.close()

    def get_today_realized(self) -> Dict[str, Any]:
        conn = self._connect()
        try:
            day = _today()
            r = conn.execute("SELECT realized_pnl, updated_ts FROM realized_day WHERE day=?", (day,)).fetchone()
            return {"day": day, "realized_pnl": float(r[0]) if r else 0.0, "updated_ts": (r[1] if r else None)}
        finally:
            conn.close()

    def last_fills(self, limit: int = 50) -> list[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, ts, venue, symbol, side, qty, price, fee, fee_ccy FROM fills ORDER BY id DESC LIMIT ?",
                (int(limit),)
            ).fetchall()
            return [
                {
                    "id": r[0],
                    "ext_id": None,
                    "ts": r[1],
                    "venue": r[2],
                    "symbol": r[3],
                    "side": r[4],
                    "qty": r[5],
                    "price": r[6],
                    "fee": r[7],
                    "fee_ccy": r[8],
                }
                for r in rows
            ]
        finally:
            conn.close()

    def positions(self) -> list[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT venue, symbol, qty, avg_price, updated_ts FROM positions ORDER BY venue, symbol"
            ).fetchall()
            return [{"venue": r[0], "symbol": r[1], "qty": r[2], "avg_price": r[3], "updated_ts": r[4]} for r in rows]
        finally:
            conn.close()
