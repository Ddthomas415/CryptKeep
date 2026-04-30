from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.execution.intent_lifecycle import (
    LIVE_QUEUE_TERMINAL_STATUSES,
    live_queue_transition_allowed,
    normalize_live_queue_status,
)
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "intent_queue.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS trade_intents (
  intent_id TEXT PRIMARY KEY,
  created_ts TEXT NOT NULL,
  ts TEXT NOT NULL,
  source TEXT NOT NULL,
  strategy_id TEXT,
  action TEXT,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  qty REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL,
  last_error TEXT,
  client_order_id TEXT,
  linked_order_id TEXT,
  meta TEXT,
  updated_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ti_status_ts ON trade_intents(status, created_ts);
CREATE INDEX IF NOT EXISTS idx_ti_symbol_ts ON trade_intents(symbol, ts);
CREATE TABLE IF NOT EXISTS consumer_state (
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
        cols = [r[1] for r in con.execute("PRAGMA table_info(trade_intents)").fetchall()]
        if cols:
            if "action" not in cols:
                con.execute("ALTER TABLE trade_intents ADD COLUMN action TEXT")
            if "meta" not in cols:
                con.execute("ALTER TABLE trade_intents ADD COLUMN meta TEXT")
    except Exception:
        pass
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con


def _decode_intent_row(row: tuple[Any, ...]) -> Dict[str, Any]:
    return {
        "intent_id": row[0], "created_ts": row[1], "ts": row[2], "source": row[3], "strategy_id": row[4],
        "action": row[5], "venue": row[6], "symbol": row[7], "side": row[8], "order_type": row[9], "qty": row[10], "limit_price": row[11],
        "status": row[12], "last_error": row[13], "client_order_id": row[14], "linked_order_id": row[15],
        "meta": json.loads(row[16]) if row[16] else None, "updated_ts": row[17],
    }


def _encode_meta(meta: Any) -> str | None:
    return json.dumps(meta) if meta is not None else None


def _fetch_intent_row(con: sqlite3.Connection, intent_id: str) -> tuple[Any, ...] | None:
    return con.execute(
        "SELECT intent_id, created_ts, ts, source, strategy_id, action, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, meta, updated_ts "
        "FROM trade_intents WHERE intent_id=?",
        (str(intent_id),),
    ).fetchone()

class IntentQueueSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert_intent(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            now = _now()
            intent_id = str(row["intent_id"])
            created_ts = str(row.get("created_ts") or now)
            meta_json = _encode_meta(row.get("meta"))
            con.execute("BEGIN IMMEDIATE")
            existing_row = _fetch_intent_row(con, intent_id)
            if existing_row is None:
                con.execute(
                    "INSERT INTO trade_intents(intent_id, created_ts, ts, source, strategy_id, action, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, meta, updated_ts) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        intent_id,
                        created_ts,
                        str(row["ts"]),
                        str(row["source"]),
                        row.get("strategy_id"),
                        row.get("action"),
                        str(row["venue"]),
                        str(row["symbol"]),
                        str(row["side"]),
                        str(row["order_type"]),
                        float(row["qty"]),
                        row.get("limit_price"),
                        normalize_live_queue_status(row["status"]),
                        row.get("last_error"),
                        row.get("client_order_id"),
                        row.get("linked_order_id"),
                        meta_json,
                        now,
                    ),
                )
                con.execute("COMMIT")
                return

            existing = _decode_intent_row(existing_row)
            current_status = normalize_live_queue_status(existing["status"])
            next_status = normalize_live_queue_status(row.get("status") or current_status)
            payload_mutable = (
                current_status == "queued"
                and not existing.get("client_order_id")
                and not existing.get("linked_order_id")
                and next_status == "queued"
            )
            status_mutable = (
                current_status not in LIVE_QUEUE_TERMINAL_STATUSES
                and live_queue_transition_allowed(current_status, next_status)
            )

            updated = {
                "intent_id": existing["intent_id"],
                "created_ts": existing["created_ts"],
                "ts": str(row["ts"]) if payload_mutable else existing["ts"],
                "source": str(row["source"]) if payload_mutable else existing["source"],
                "strategy_id": row.get("strategy_id") if payload_mutable else existing["strategy_id"],
                "action": row.get("action") if payload_mutable else existing["action"],
                "venue": str(row["venue"]) if payload_mutable else existing["venue"],
                "symbol": str(row["symbol"]) if payload_mutable else existing["symbol"],
                "side": str(row["side"]) if payload_mutable else existing["side"],
                "order_type": str(row["order_type"]) if payload_mutable else existing["order_type"],
                "qty": float(row["qty"]) if payload_mutable else existing["qty"],
                "limit_price": row.get("limit_price") if payload_mutable else existing["limit_price"],
                "status": next_status if status_mutable else current_status,
                "last_error": (
                    row.get("last_error")
                    if (payload_mutable or status_mutable)
                    else existing["last_error"]
                ),
                "client_order_id": existing.get("client_order_id") or row.get("client_order_id"),
                "linked_order_id": existing.get("linked_order_id") or row.get("linked_order_id"),
                "meta": (
                    row.get("meta")
                    if (payload_mutable or status_mutable)
                    else existing["meta"]
                ),
                "updated_ts": now,
            }
            changed = any(updated[key] != existing.get(key) for key in updated if key != "updated_ts")
            if changed:
                con.execute(
                    "UPDATE trade_intents SET created_ts=?, ts=?, source=?, strategy_id=?, action=?, venue=?, symbol=?, side=?, order_type=?, qty=?, limit_price=?, status=?, last_error=?, client_order_id=?, linked_order_id=?, meta=?, updated_ts=? WHERE intent_id=?",
                    (
                        updated["created_ts"],
                        updated["ts"],
                        updated["source"],
                        updated["strategy_id"],
                        updated["action"],
                        updated["venue"],
                        updated["symbol"],
                        updated["side"],
                        updated["order_type"],
                        updated["qty"],
                        updated["limit_price"],
                        updated["status"],
                        updated["last_error"],
                        updated["client_order_id"],
                        updated["linked_order_id"],
                        _encode_meta(updated["meta"]),
                        updated["updated_ts"],
                        intent_id,
                    ),
                )
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            con.close()

    def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT intent_id, created_ts, ts, source, strategy_id, action, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, meta, updated_ts FROM trade_intents WHERE intent_id=?",
                (str(intent_id),),
            ).fetchone()
            if not r:
                return None
            return _decode_intent_row(r)
        finally:
            con.close()

    def list_intents(self, limit: int = 500, status: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT intent_id, created_ts, ts, source, strategy_id, action, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, meta, updated_ts "
                 "FROM trade_intents")
            args = []
            if status:
                q += " WHERE status=?"
                args.append(str(status))
            q += " ORDER BY created_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [_decode_intent_row(r) for r in rows]
        finally:
            con.close()

    def next_queued(self, limit: int = 20) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                ("SELECT intent_id, created_ts, ts, source, strategy_id, action, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, meta, updated_ts "
                 "FROM trade_intents WHERE status='queued' ORDER BY created_ts ASC LIMIT ?"),
                (int(limit),),
            ).fetchall()
            return [_decode_intent_row(r) for r in rows]
        finally:
            con.close()

    def claim_next_queued(self, limit: int = 20) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            rows = con.execute(
                ("SELECT intent_id, created_ts, ts, source, strategy_id, action, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, meta, updated_ts "
                 "FROM trade_intents WHERE status='queued' ORDER BY created_ts ASC LIMIT ?"),
                (int(limit),),
            ).fetchall()
            claimed = []
            now = _now()
            for r in rows:
                item = _decode_intent_row(r)
                intent_id = str(item["intent_id"])
                client_order_id = str(item.get("client_order_id") or f"paper_intent_{intent_id}")
                cur = con.execute(
                    """
                    UPDATE trade_intents
                       SET status='submitting', client_order_id=?, updated_ts=?
                     WHERE intent_id=?
                       AND status='queued'
                    """,
                    (client_order_id, now, intent_id),
                )
                if cur.rowcount != 1:
                    continue
                item["status"] = "submitting"
                item["client_order_id"] = client_order_id
                item["updated_ts"] = now
                claimed.append(item)
            con.execute("COMMIT")
            return claimed
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            con.close()

    def update_status(self, intent_id: str, status: str, *, last_error: str | None = None, client_order_id: str | None = None, linked_order_id: str | None = None) -> bool:
        con = _connect()
        try:
            nxt = normalize_live_queue_status(status)
            cur = con.execute(
                """
                UPDATE trade_intents
                   SET status=?, last_error=?, client_order_id=COALESCE(?, client_order_id), linked_order_id=COALESCE(?, linked_order_id), updated_ts=?
                 WHERE intent_id=?
                   AND status NOT IN ('filled', 'rejected', 'canceled', 'cancelled', 'error')
                   AND (
                        status = ?
                     OR (status = 'queued' AND ? IN ('submitting', 'submitted', 'rejected', 'held'))
                     OR (status = 'submitting' AND ? IN ('submitted', 'rejected'))
                     OR (status = 'submitted' AND ? IN ('filled', 'canceled', 'cancelled', 'rejected', 'error', 'held'))
                     OR (status = 'held' AND ? IN ('queued', 'rejected'))
                   )
                """,
                (
                    nxt,
                    last_error,
                    client_order_id,
                    linked_order_id,
                    _now(),
                    str(intent_id),
                    nxt,
                    nxt,
                    nxt,
                    nxt,
                    nxt,
                ),
            )
            con.commit()
            return cur.rowcount == 1
        finally:
            con.close()

    def get_state(self, k: str) -> Optional[str]:
        con = _connect()
        try:
            r = con.execute("SELECT v FROM consumer_state WHERE k=?", (str(k),)).fetchone()
            return r[0] if r else None
        finally:
            con.close()

    def set_state(self, k: str, v: str) -> None:
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO consumer_state(k,v) VALUES(?,?)", (str(k), str(v)))
        finally:
            con.close()
