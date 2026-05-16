from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from services.execution.intent_lifecycle import normalize_live_queue_status
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "live_intent_queue.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS live_trade_intents (
  intent_id TEXT PRIMARY KEY,
  created_ts TEXT NOT NULL,
  ts TEXT NOT NULL,
  source TEXT NOT NULL,
  strategy_id TEXT,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  qty REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL,
  last_error TEXT,
  client_order_id TEXT,
  exchange_order_id TEXT,
  meta TEXT,
  updated_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lti_status_ts ON live_trade_intents(status, created_ts);
CREATE INDEX IF NOT EXISTS idx_lti_symbol_ts ON live_trade_intents(symbol, ts);
CREATE TABLE IF NOT EXISTS live_consumer_state (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(live_trade_intents)").fetchall()]
        if cols:
            if "strategy_id" not in cols:
                con.execute("ALTER TABLE live_trade_intents ADD COLUMN strategy_id TEXT")
            if "meta" not in cols:
                con.execute("ALTER TABLE live_trade_intents ADD COLUMN meta TEXT")
    except Exception:
        pass
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class LiveIntentQueueSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert_intent(self, row: Dict[str, Any]) -> None:
        terminal = ("filled", "rejected", "canceled", "cancelled", "error")
        intent_id = str(row["intent_id"])
        meta_json = json.dumps(row.get("meta")) if row.get("meta") is not None else None
        now = _now()

        con = _connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO live_trade_intents(intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, exchange_order_id, meta, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    intent_id,
                    str(row.get("created_ts") or now),
                    str(row["ts"]),
                    str(row["source"]),
                    row.get("strategy_id"),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    str(row["order_type"]),
                    float(row["qty"]),
                    row.get("limit_price"),
                    str(row["status"]),
                    row.get("last_error"),
                    row.get("client_order_id"),
                    row.get("exchange_order_id"),
                    meta_json,
                    now,
                ),
            )
            placeholders = ",".join("?" for _ in terminal)
            con.execute(
                f"UPDATE live_trade_intents SET ts=?, source=?, strategy_id=?, venue=?, symbol=?, side=?, order_type=?, qty=?, limit_price=?, status=?, client_order_id=COALESCE(?, client_order_id), exchange_order_id=COALESCE(?, exchange_order_id), meta=?, updated_ts=? "
                f"WHERE intent_id=? AND status NOT IN ({placeholders})",
                (
                    str(row["ts"]),
                    str(row["source"]),
                    row.get("strategy_id"),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    str(row["order_type"]),
                    float(row["qty"]),
                    row.get("limit_price"),
                    str(row["status"]),
                    row.get("client_order_id"),
                    row.get("exchange_order_id"),
                    meta_json,
                    now,
                    intent_id,
                    *terminal,
                ),
            )
        finally:
            con.close()

    def list_intents(self, limit: int = 500, status: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, exchange_order_id, meta, updated_ts "
                 "FROM live_trade_intents")
            args = []
            if status:
                q += " WHERE status=?"
                args.append(str(status))
            q += " ORDER BY created_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "intent_id": r[0], "created_ts": r[1], "ts": r[2], "source": r[3], "strategy_id": r[4], "venue": r[5], "symbol": r[6],
                    "side": r[7], "order_type": r[8], "qty": r[9], "limit_price": r[10], "status": r[11],
                    "last_error": r[12], "client_order_id": r[13], "exchange_order_id": r[14],
                    "meta": json.loads(r[15]) if r[15] else None, "updated_ts": r[16],
                }
                for r in rows
            ]
        finally:
            con.close()

    def next_queued(self, limit: int = 20) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                ("SELECT intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, exchange_order_id, meta, updated_ts "
                 "FROM live_trade_intents WHERE status='queued' ORDER BY created_ts ASC LIMIT ?"),
                (int(limit),),
            ).fetchall()
            return [
                {
                    "intent_id": r[0], "created_ts": r[1], "ts": r[2], "source": r[3], "strategy_id": r[4], "venue": r[5], "symbol": r[6],
                    "side": r[7], "order_type": r[8], "qty": r[9], "limit_price": r[10], "status": r[11],
                    "last_error": r[12], "client_order_id": r[13], "exchange_order_id": r[14],
                    "meta": json.loads(r[15]) if r[15] else None, "updated_ts": r[16],
                }
                for r in rows
            ]
        finally:
            con.close()

    def update_status(self, intent_id: str, status: str, *, last_error: str | None = None, client_order_id: str | None = None, exchange_order_id: str | None = None) -> bool:
        con = _connect()
        try:
            nxt = normalize_live_queue_status(status)

            cur = con.execute(
                """
                UPDATE live_trade_intents
                   SET status=?, last_error=?, client_order_id=?, exchange_order_id=?, updated_ts=?
                 WHERE intent_id=?
                   AND status NOT IN ('filled', 'rejected', 'canceled', 'cancelled', 'error')
                   AND (
                        status = ?
                     OR (status = 'queued' AND ? IN ('submitted', 'rejected', 'held'))
                     OR (status = 'submitted' AND ? IN ('filled', 'canceled', 'cancelled', 'rejected', 'error', 'held'))
                     OR (status = 'held' AND ? IN ('queued', 'rejected'))
                   )
                """,
                (
                    str(nxt),
                    last_error,
                    client_order_id,
                    exchange_order_id,
                    _now(),
                    str(intent_id),
                    str(nxt),
                    str(nxt),
                    str(nxt),
                    str(nxt),
                ),
            )
            con.commit()
            return cur.rowcount == 1
        finally:
            con.close()


    def get_state(self, k: str) -> Optional[str]:
        con = _connect()
        try:
            r = con.execute("SELECT v FROM live_consumer_state WHERE k=?", (str(k),)).fetchone()
            return r[0] if r else None
        finally:
            con.close()

    def atomic_risk_claim(
        self,
        *,
        max_trades: int,
        max_notional: float,
        notional_est: float,
    ) -> tuple[bool, str | None]:
        """Check limits and increment counters atomically under BEGIN IMMEDIATE.
        Day-rollover and min-notional checks remain in application code.
        Returns (True, None) if within limits and counters incremented.
        Returns (False, reason) if any limit exceeded — no mutation occurs."""
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            def _get(k: str) -> str:
                r = con.execute(
                    "SELECT v FROM live_consumer_state WHERE k=?", (k,)
                ).fetchone()
                return r[0] if r else "0"
            trades = int(float(_get("risk:trades")))
            notional = float(_get("risk:notional"))
            if max_trades > 0 and trades >= max_trades:
                con.execute("ROLLBACK")
                return False, "risk:max_trades_per_day"
            if max_notional > 0 and notional + notional_est > max_notional:
                con.execute("ROLLBACK")
                return False, "risk:max_daily_notional_quote"
            con.execute(
                "INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)",
                ("risk:trades", str(trades + 1)),
            )
            con.execute(
                "INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)",
                ("risk:notional", str(notional + float(notional_est))),
            )
            con.execute("COMMIT")
            return True, None
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            con.close()

    def set_state(self, k: str, v: str) -> None:
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)", (str(k), str(v)))
            con.commit()
        finally:
            con.close()
