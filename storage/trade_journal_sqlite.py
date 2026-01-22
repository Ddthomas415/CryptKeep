from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "trade_journal.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS journal_fills (
  fill_id TEXT PRIMARY KEY,
  journal_ts TEXT NOT NULL,
  intent_id TEXT,
  source TEXT,
  strategy_id TEXT,
  client_order_id TEXT,
  order_id TEXT NOT NULL,
  fill_ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL NOT NULL,
  fee_currency TEXT NOT NULL,
  cash_quote REAL,
  pos_qty REAL,
  pos_avg_price REAL,
  realized_pnl_total REAL
);
CREATE INDEX IF NOT EXISTS idx_jf_ts ON journal_fills(journal_ts);
CREATE INDEX IF NOT EXISTS idx_jf_symbol ON journal_fills(symbol);
CREATE INDEX IF NOT EXISTS idx_jf_intent ON journal_fills(intent_id);
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

class TradeJournalSQLite:
    def __init__(self) -> None:
        _connect().close()

    def insert_fill(self, row: dict) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO journal_fills(fill_id, journal_ts, intent_id, source, strategy_id, client_order_id, order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency, cash_quote, pos_qty, pos_avg_price, realized_pnl_total) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["fill_id"]),
                    str(row.get("journal_ts") or _now()),
                    row.get("intent_id"),
                    row.get("source"),
                    row.get("strategy_id"),
                    row.get("client_order_id"),
                    str(row["order_id"]),
                    str(row["fill_ts"]),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    float(row["qty"]),
                    float(row["price"]),
                    float(row["fee"]),
                    str(row["fee_currency"]),
                    row.get("cash_quote"),
                    row.get("pos_qty"),
                    row.get("pos_avg_price"),
                    row.get("realized_pnl_total"),
                ),
            )
        finally:
            con.close()

   
    def list_fills_all(self, limit: int = 200000) -> list[dict]:
        # Convenience: fetch a large window for analytics/export
        return self.list_fills(limit=int(limit))

 def list_fills(self, limit: int = 1000) -> list[dict]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT fill_id, journal_ts, intent_id, source, strategy_id, client_order_id, order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency, cash_quote, pos_qty, pos_avg_price, realized_pnl_total "
                "FROM journal_fills ORDER BY journal_ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            out = []
            for r in rows:
                out.append({
                    "fill_id": r[0], "journal_ts": r[1], "intent_id": r[2], "source": r[3], "strategy_id": r[4],
                    "client_order_id": r[5], "order_id": r[6], "fill_ts": r[7], "venue": r[8], "symbol": r[9], "side": r[10],
                    "qty": r[11], "price": r[12], "fee": r[13], "fee_currency": r[14],
                    "cash_quote": r[15], "pos_qty": r[16], "pos_avg_price": r[17], "realized_pnl_total": r[18],
                })
            return out
        finally:
            con.close()

    def count(self) -> int:
        con = _connect()
        try:
            r = con.execute("SELECT COUNT(1) FROM journal_fills").fetchone()
            return int(r[0] if r else 0)
        finally:
            con.close()
