from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "live_trading.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS live_orders (
  client_order_id TEXT PRIMARY KEY,
  created_ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  qty REAL NOT NULL,
  limit_price REAL,
  exchange_order_id TEXT,
  status TEXT NOT NULL,
  last_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_lo_created ON live_orders(created_ts);
CREATE INDEX IF NOT EXISTS idx_lo_symbol ON live_orders(symbol);
CREATE TABLE IF NOT EXISTS live_fills (
  fill_key TEXT PRIMARY KEY,
  trade_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL,
  fee_currency TEXT,
  client_order_id TEXT,
  exchange_order_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_lf_ts ON live_fills(ts);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fill_key(venue: Any, symbol: Any, trade_id: Any) -> str:
    return json.dumps([str(venue), str(symbol), str(trade_id)], separators=(",", ":"))

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)

    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(live_fills)").fetchall()]
        if cols and "fill_key" not in cols:
            con.execute("BEGIN IMMEDIATE")
            con.execute("ALTER TABLE live_fills RENAME TO live_fills_legacy")
            con.execute(
                """
                CREATE TABLE live_fills (
                  fill_key TEXT PRIMARY KEY,
                  trade_id TEXT NOT NULL,
                  ts TEXT NOT NULL,
                  venue TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  side TEXT NOT NULL,
                  qty REAL NOT NULL,
                  price REAL NOT NULL,
                  fee REAL,
                  fee_currency TEXT,
                  client_order_id TEXT,
                  exchange_order_id TEXT
                )
                """
            )
            legacy_rows = con.execute(
                """
                SELECT trade_id, ts, venue, symbol, side, qty, price, fee,
                       fee_currency, client_order_id, exchange_order_id
                FROM live_fills_legacy
                """
            ).fetchall()
            for r in legacy_rows:
                con.execute(
                    """
                    INSERT OR IGNORE INTO live_fills(
                      fill_key, trade_id, ts, venue, symbol, side, qty, price, fee,
                      fee_currency, client_order_id, exchange_order_id
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        _fill_key(r[2], r[3], r[0]),
                        r[0],
                        r[1],
                        r[2],
                        r[3],
                        r[4],
                        r[5],
                        r[6],
                        r[7],
                        r[8],
                        r[9],
                        r[10],
                    ),
                )
            con.execute("DROP TABLE live_fills_legacy")
            con.execute("CREATE INDEX IF NOT EXISTS idx_lf_ts ON live_fills(ts)")
            con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return con

class LiveTradingSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert_order(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO live_orders(client_order_id, created_ts, venue, symbol, side, order_type, qty, limit_price, exchange_order_id, status, last_error) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["client_order_id"]),
                    str(row.get("created_ts") or _now()),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    str(row["order_type"]),
                    float(row["qty"]),
                    row.get("limit_price"),
                    row.get("exchange_order_id"),
                    str(row["status"]),
                    row.get("last_error"),
                ),
            )
        finally:
            con.close()

    def list_orders(self, limit: int = 300) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT client_order_id, created_ts, venue, symbol, side, order_type, qty, limit_price, exchange_order_id, status, last_error "
                "FROM live_orders ORDER BY created_ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [
                {
                    "client_order_id": r[0], "created_ts": r[1], "venue": r[2], "symbol": r[3], "side": r[4],
                    "order_type": r[5], "qty": r[6], "limit_price": r[7], "exchange_order_id": r[8], "status": r[9], "last_error": r[10],
                }
                for r in rows
            ]
        finally:
            con.close()

    def insert_fill(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO live_fills(fill_key, trade_id, ts, venue, symbol, side, qty, price, fee, fee_currency, client_order_id, exchange_order_id) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    _fill_key(row["venue"], row["symbol"], row["trade_id"]),
                    str(row["trade_id"]),
                    str(row["ts"]),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    float(row["qty"]),
                    float(row["price"]),
                    row.get("fee"),
                    row.get("fee_currency"),
                    row.get("client_order_id"),
                    row.get("exchange_order_id"),
                ),
            )
        finally:
            con.close()

    def list_fills(self, limit: int = 300) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT trade_id, ts, venue, symbol, side, qty, price, fee, fee_currency, client_order_id, exchange_order_id "
                "FROM live_fills ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [
                {
                    "trade_id": r[0], "ts": r[1], "venue": r[2], "symbol": r[3], "side": r[4], "qty": r[5],
                    "price": r[6], "fee": r[7], "fee_currency": r[8], "client_order_id": r[9], "exchange_order_id": r[10],
                }
                for r in rows
            ]
        finally:
            con.close()
