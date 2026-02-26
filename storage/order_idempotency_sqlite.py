from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "order_idempotency.sqlite"

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS order_idempotency (
  intent_id TEXT PRIMARY KEY,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  client_order_id TEXT NOT NULL,
  client_param_key TEXT NOT NULL,
  exchange_order_id TEXT,
  status TEXT NOT NULL,
  created_ts TEXT NOT NULL,
  last_update_ts TEXT NOT NULL,
  last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_oid_venue ON order_idempotency(venue);
CREATE INDEX IF NOT EXISTS idx_oid_client ON order_idempotency(venue, client_order_id);
'''

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

class OrderIdempotencySQLite:
    def __init__(self) -> None:
        _connect().close()

    def get(self, intent_id: str) -> Optional[dict]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT intent_id, venue, symbol, side, qty, price, client_order_id, client_param_key, exchange_order_id, status, created_ts, last_update_ts, last_error "
                "FROM order_idempotency WHERE intent_id=?",
                (str(intent_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "intent_id": r[0], "venue": r[1], "symbol": r[2], "side": r[3], "qty": r[4], "price": r[5],
                "client_order_id": r[6], "client_param_key": r[7], "exchange_order_id": r[8],
                "status": r[9], "created_ts": r[10], "last_update_ts": r[11], "last_error": r[12],
            }
        finally:
            con.close()

    def upsert_new(self, row: dict) -> dict:
        con = _connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO order_idempotency(intent_id, venue, symbol, side, qty, price, client_order_id, client_param_key, exchange_order_id, status, created_ts, last_update_ts, last_error) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["intent_id"]), str(row["venue"]), str(row["symbol"]), str(row["side"]),
                    float(row["qty"]), float(row["price"]),
                    str(row["client_order_id"]), str(row["client_param_key"]),
                    row.get("exchange_order_id"), str(row.get("status","pending")),
                    str(row.get("created_ts") or _now()), str(row.get("last_update_ts") or _now()),
                    row.get("last_error"),
                )
            )
            return self.get(str(row["intent_id"])) or row
        finally:
            con.close()

    def update(self, intent_id: str, **fields) -> None:
        if not fields:
            return
        fields = dict(fields)
        fields["last_update_ts"] = _now()
        sets = ", ".join([f"{k}=?" for k in fields.keys()])
        vals = list(fields.values()) + [str(intent_id)]
        con = _connect()
        try:
            con.execute(f"UPDATE order_idempotency SET {sets} WHERE intent_id=?", tuple(vals))
        finally:
            con.close()
