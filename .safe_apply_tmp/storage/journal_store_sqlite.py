from __future__ import annotations
import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from core.models import Fill, OrderAck, OrderStatus, PortfolioState, Position, Side
from core.symbols import normalize_symbol

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

SCHEMA_V1 = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol_norm TEXT NOT NULL,
  client_order_id TEXT NOT NULL,
  venue_order_id TEXT,
  status TEXT NOT NULL,
  message TEXT
);
CREATE INDEX IF NOT EXISTS idx_orders_ts ON orders(ts);
CREATE INDEX IF NOT EXISTS idx_orders_venue_symbol ON orders(venue, symbol_norm);
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_client ON orders(venue, client_order_id);
CREATE TABLE IF NOT EXISTS fills (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol_norm TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL NOT NULL,
  client_order_id TEXT NOT NULL,
  venue_order_id TEXT,
  fill_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_fills_ts ON fills(ts);
CREATE INDEX IF NOT EXISTS idx_fills_venue_symbol ON fills(venue, symbol_norm);
CREATE UNIQUE INDEX IF NOT EXISTS idx_fills_unique ON fills(venue, symbol_norm, fill_id) WHERE fill_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS positions (
  venue TEXT NOT NULL,
  symbol_norm TEXT NOT NULL,
  qty REAL NOT NULL,
  avg_price REAL NOT NULL,
  realized_pnl REAL NOT NULL,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (venue, symbol_norm)
);
"""

class JournalStoreSQLite:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_or_upgrade()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_or_upgrade(self) -> None:
        conn = self._connect()
        try:
            v = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if v < 1:
                for stmt in SCHEMA_V1.strip().split(";"):
                    s = stmt.strip()
                    if s:
                        conn.execute(s)
                conn.execute("PRAGMA user_version = 1")
        finally:
            conn.close()

    async def record_order_ack(self, ack: OrderAck, symbol: Optional[str] = None, venue: Optional[str] = None) -> None:
        await asyncio.to_thread(self._record_order_ack_sync, ack, symbol, venue)

    def _record_order_ack_sync(self, ack: OrderAck, symbol: Optional[str], venue: Optional[str]) -> None:
        v = venue or "unknown"
        symn = normalize_symbol(v, symbol or "UNKNOWN")
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO orders(ts, venue, symbol_norm, client_order_id, venue_order_id, status, message) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    ack.ts.isoformat(),
                    v,
                    symn,
                    ack.client_order_id,
                    ack.venue_order_id,
                    ack.status.value if isinstance(ack.status, OrderStatus) else str(ack.status),
                    ack.message,
                ),
            )
        finally:
            conn.close()

    async def record_fill(self, fill: Fill) -> None:
        await asyncio.to_thread(self._record_fill_sync, fill)

    def _record_fill_sync(self, fill: Fill) -> None:
        symn = normalize_symbol(fill.venue, fill.symbol)
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO fills(ts, venue, symbol_norm, side, qty, price, fee, client_order_id, venue_order_id, fill_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    fill.ts.isoformat(),
                    fill.venue,
                    symn,
                    fill.side.value if isinstance(fill.side, Side) else str(fill.side),
                    float(fill.qty),
                    float(fill.price),
                    float(fill.fee),
                    fill.client_order_id,
                    fill.venue_order_id,
                    fill.fill_id,
                ),
            )
            cur = conn.execute(
                "SELECT qty, avg_price, realized_pnl FROM positions WHERE venue=? AND symbol_norm=?",
                (fill.venue, symn),
            )
            row = cur.fetchone()
            qty = float(row[0]) if row else 0.0
            avg = float(row[1]) if row else 0.0
            realized = float(row[2]) if row else 0.0
            fqty = float(fill.qty)
            fpx = float(fill.price)
            fee = float(fill.fee)
            side = fill.side.value if isinstance(fill.side, Side) else str(fill.side)
            def set_position(nqty: float, navg: float, nreal: float) -> None:
                conn.execute(
                    "INSERT OR REPLACE INTO positions(venue, symbol_norm, qty, avg_price, realized_pnl, updated_ts) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (fill.venue, symn, nqty, navg, nreal, utc_now_iso()),
                )
            if side == "buy":
                if qty >= 0:
                    nqty = qty + fqty
                    navg = (avg * qty + fpx * fqty) / nqty if nqty != 0 else 0.0
                    set_position(nqty, navg, realized)
                else:
                    closing = min(fqty, -qty)
                    realized += (avg - fpx) * closing
                    qty += closing
                    remaining = fqty - closing
                    if abs(qty) < 1e-12:
                        qty = 0.0
                        avg = 0.0
                    if remaining > 0:
                        qty = remaining
                        avg = fpx
                    set_position(qty, avg, realized)
            elif side == "sell":
                if qty <= 0:
                    nqty = qty - fqty
                    abs_qty = abs(qty)
                    abs_nqty = abs(nqty)
                    navg = (avg * abs_qty + fpx * fqty) / abs_nqty if abs_nqty != 0 else 0.0
                    set_position(nqty, navg, realized)
                else:
                    closing = min(fqty, qty)
                    realized += (fpx - avg) * closing
                    qty -= closing
                    remaining = fqty - closing
                    if abs(qty) < 1e-12:
                        qty = 0.0
                        avg = 0.0
                    if remaining > 0:
                        qty = -remaining
                        avg = fpx
                    set_position(qty, avg, realized)
        finally:
            conn.close()

    async def load_portfolio(self) -> PortfolioState:
        return await asyncio.to_thread(self._load_portfolio_sync)

    def _load_portfolio_sync(self) -> PortfolioState:
        conn = self._connect()
        try:
            ps = PortfolioState()
            cur = conn.execute("SELECT venue, symbol_norm, qty, avg_price FROM positions")
            for venue, symn, qty, avg in cur.fetchall():
                key = f"{venue}:{symn}"
                ps.positions[key] = Position(
                    venue=str(venue),
                    symbol=str(symn),
                    qty=float(qty),
                    avg_price=float(avg),
                    unrealized_pnl=0.0,
                )
            return ps
        finally:
            conn.close()
