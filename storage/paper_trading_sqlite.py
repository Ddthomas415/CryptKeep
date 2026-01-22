from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "paper_trading.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS paper_state (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paper_orders (
  order_id TEXT PRIMARY KEY,
  client_order_id TEXT NOT NULL UNIQUE, -- idempotency key
  created_ts TEXT NOT NULL,
  ts TEXT NOT NULL, -- intended timestamp
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  qty REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL,
  reject_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_po_ts ON paper_orders(ts);
CREATE INDEX IF NOT EXISTS idx_po_symbol ON paper_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_po_status ON paper_orders(status);
CREATE TABLE IF NOT EXISTS paper_fills (
  fill_id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  price REAL NOT NULL,
  qty REAL NOT NULL,
  fee REAL NOT NULL,
  fee_currency TEXT NOT NULL,
  FOREIGN KEY(order_id) REFERENCES paper_orders(order_id)
);
CREATE INDEX IF NOT EXISTS idx_pf_order ON paper_fills(order_id);
CREATE INDEX IF NOT EXISTS idx_pf_ts ON paper_fills(ts);
CREATE TABLE IF NOT EXISTS paper_positions (
  symbol TEXT PRIMARY KEY,
  qty REAL NOT NULL,
  avg_price REAL NOT NULL,
  realized_pnl REAL NOT NULL,
  updated_ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paper_equity (
  ts TEXT PRIMARY KEY,
  cash_quote REAL NOT NULL,
  equity_quote REAL NOT NULL,
  unrealized_pnl REAL NOT NULL,
  realized_pnl REAL NOT NULL
);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class PaperTradingSQLite:
    def __init__(self) -> None:
        _connect().close()

    def get_state(self, k: str) -> Optional[str]:
        con = _connect()
        try:
            r = con.execute("SELECT v FROM paper_state WHERE k=?", (str(k),)).fetchone()
            return r[0] if r else None
        finally:
            con.close()

    def set_state(self, k: str, v: str) -> None:
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO paper_state(k,v) VALUES(?,?)", (str(k), str(v)))
        finally:
            con.close()

    def insert_order(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_orders(order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["order_id"]),
                    str(row["client_order_id"]),
                    _now(),
                    str(row["ts"]),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    str(row["order_type"]),
                    float(row["qty"]),
                    row.get("limit_price"),
                    str(row["status"]),
                    row.get("reject_reason"),
                ),
            )
        finally:
            con.close()

    def get_order_by_client_id(self, client_order_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason "
                "FROM paper_orders WHERE client_order_id=?",
                (str(client_order_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "order_id": r[0], "client_order_id": r[1], "created_ts": r[2], "ts": r[3],
                "venue": r[4], "symbol": r[5], "side": r[6], "order_type": r[7],
                "qty": r[8], "limit_price": r[9], "status": r[10], "reject_reason": r[11],
            }
        finally:
            con.close()

    def update_order_status(self, order_id: str, status: str, reject_reason: str | None = None) -> None:
        con = _connect()
        try:
            con.execute("UPDATE paper_orders SET status=?, reject_reason=? WHERE order_id=?", (str(status), reject_reason, str(order_id)))
        finally:
            con.close()

    def list_orders(self, limit: int = 500, status: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason "
                 "FROM paper_orders")
            args = []
            if status:
                q += " WHERE status=?"
                args.append(str(status))
            q += " ORDER BY created_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "order_id": r[0], "client_order_id": r[1], "created_ts": r[2], "ts": r[3],
                    "venue": r[4], "symbol": r[5], "side": r[6], "order_type": r[7],
                    "qty": r[8], "limit_price": r[9], "status": r[10], "reject_reason": r[11],
                }
                for r in rows
            ]
        finally:
            con.close()

    def insert_fill(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_fills(fill_id, order_id, ts, price, qty, fee, fee_currency) VALUES(?,?,?,?,?,?,?)",
                (str(row["fill_id"]), str(row["order_id"]), str(row["ts"]), float(row["price"]), float(row["qty"]), float(row["fee"]), str(row["fee_currency"])),
            )
        finally:
            con.close()

    def list_fills(self, limit: int = 500) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT fill_id, order_id, ts, price, qty, fee, fee_currency FROM paper_fills ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [{"fill_id": r[0], "order_id": r[1], "ts": r[2], "price": r[3], "qty": r[4], "fee": r[5], "fee_currency": r[6]} for r in rows]
        finally:
            con.close()

    def upsert_position(self, symbol: str, qty: float, avg_price: float, realized_pnl: float) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_positions(symbol, qty, avg_price, realized_pnl, updated_ts) VALUES(?,?,?,?,?)",
                (str(symbol), float(qty), float(avg_price), float(realized_pnl), _now()),
            )
        finally:
            con.close()

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute("SELECT symbol, qty, avg_price, realized_pnl, updated_ts FROM paper_positions WHERE symbol=?", (str(symbol),)).fetchone()
            if not r:
                return None
            return {"symbol": r[0], "qty": r[1], "avg_price": r[2], "realized_pnl": r[3], "updated_ts": r[4]}
        finally:
            con.close()

    def list_positions(self, limit: int = 200) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT symbol, qty, avg_price, realized_pnl, updated_ts FROM paper_positions ORDER BY updated_ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [{"symbol": r[0], "qty": r[1], "avg_price": r[2], "realized_pnl": r[3], "updated_ts": r[4]} for r in rows]
        finally:
            con.close()

    def insert_equity(self, ts: str, cash_quote: float, equity_quote: float, unrealized_pnl: float, realized_pnl: float) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_equity(ts, cash_quote, equity_quote, unrealized_pnl, realized_pnl) VALUES(?,?,?,?,?)",
                (str(ts), float(cash_quote), float(equity_quote), float(unrealized_pnl), float(realized_pnl)),
            )
        finally:
            con.close()

   
    def get_order_by_order_id(self, order_id: str) -> Optional[dict]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason "
                "FROM paper_orders WHERE order_id=?",
                (str(order_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "order_id": r[0], "client_order_id": r[1], "created_ts": r[2], "ts": r[3],
                "venue": r[4], "symbol": r[5], "side": r[6], "order_type": r[7],
                "qty": r[8], "limit_price": r[9], "status": r[10], "reject_reason": r[11],
            }
        finally:
            con.close()

    def list_fills_for_order(self, order_id: str, limit: int = 2000) -> list[dict]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT fill_id, order_id, ts, price, qty, fee, fee_currency FROM paper_fills WHERE order_id=? ORDER BY ts ASC LIMIT ?",
                (str(order_id), int(limit)),
            ).fetchall()
            out = []
            for r in rows:
                out.append({"fill_id": r[0], "order_id": r[1], "ts": r[2], "price": r[3], "qty": r[4], "fee": r[5], "fee_currency": r[6]})
            return out
        finally:
            con.close()

 def list_equity(self, limit: int = 2000) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT ts, cash_quote, equity_quote, unrealized_pnl, realized_pnl FROM paper_equity ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [{"ts": r[0], "cash_quote": r[1], "equity_quote": r[2], "unrealized_pnl": r[3], "realized_pnl": r[4]} for r in rows]
        finally:
            con.close()
