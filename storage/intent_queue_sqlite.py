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
CREATE TABLE IF NOT EXISTS paper_exit_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  intent_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  event TEXT NOT NULL,
  reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_paper_exit_events_intent ON paper_exit_events(intent_id, event_id);
CREATE TABLE IF NOT EXISTS paper_buy_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  intent_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  event TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_paper_buy_events_intent ON paper_buy_events(intent_id, event_id);
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
                from services.execution.paper_exit_retry import has_exit_marker, exit_identity
                client_order_id = row.get("client_order_id")
                if has_exit_marker(row):
                    if row.get("source") != "strategy":
                        raise ValueError("pending_exit_strategy_source_required")
                    _identity, client_order_id = exit_identity(row)
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
                        client_order_id,
                        row.get("linked_order_id"),
                        meta_json,
                        now,
                    ),
                )
                if str(row["side"]).strip().lower() == "buy":
                    con.execute(
                        "INSERT INTO paper_buy_events(intent_id,ts,event,status,reason) VALUES(?,?,?,?,?)",
                        (intent_id, now, "created", normalize_live_queue_status(row["status"]), None),
                    )
                con.execute("COMMIT")
                return

            existing = _decode_intent_row(existing_row)
            from services.execution.paper_exit_retry import has_exit_marker
            frozen_exit = has_exit_marker(existing)
            current_status = normalize_live_queue_status(existing["status"])
            next_status = normalize_live_queue_status(row.get("status") or current_status)
            payload_mutable = (
                current_status == "queued"
                and not frozen_exit
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
                    if (payload_mutable or status_mutable) and not frozen_exit
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

    def list_paper_exits(self, *, symbol: str | None = None) -> List[Dict[str, Any]]:
        from services.execution.paper_exit_retry import has_exit_marker, exit_identity
        con = _connect()
        try:
            ids = con.execute(
                "SELECT intent_id FROM trade_intents WHERE source='strategy' AND side='sell' "
                "AND status IN ('queued','submitting','submitted','held','rejected') "
                "AND (? IS NULL OR symbol=?) ORDER BY created_ts, intent_id", (symbol, symbol),
            ).fetchall()
            rows = [_decode_intent_row(_fetch_intent_row(con, row[0])) for row in ids]
            marked = [row for row in rows if has_exit_marker(row)]
            for row in marked:
                exit_identity(row)
            return marked
        finally:
            con.close()

    def paper_exit_transition(self, intent_id: str, status: str, *, event: str,
                              reason: str | None = None, linked_order_id: str | None = None) -> bool:
        from services.execution.paper_exit_retry import exit_identity, has_exit_marker
        if status not in ("queued", "held", "submitted", "filled", "superseded"):
            raise ValueError("invalid_paper_exit_transition")
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            stored = _fetch_intent_row(con, str(intent_id))
            if stored is None:
                raise ValueError("pending_exit_missing")
            row = _decode_intent_row(stored)
            if status == "held" and has_exit_marker(row):
                # Quarantine malformed evidence without granting submission.
                pass
            else:
                exit_identity(row)
            if row["status"] in ("filled", "superseded"):
                con.execute("COMMIT")
                return False
            if row["status"] not in ("queued", "submitting", "submitted", "held", "rejected"):
                raise ValueError("pending_exit_state_not_retryable")
            con.execute(
                "UPDATE trade_intents SET status=?, last_error=?, linked_order_id=COALESCE(?, linked_order_id), "
                "updated_ts=? WHERE intent_id=?",
                (status, reason, linked_order_id, _now(), str(intent_id)),
            )
            con.execute("INSERT INTO paper_exit_events(intent_id,ts,event,reason) VALUES(?,?,?,?)",
                        (str(intent_id), _now(), str(event), reason))
            con.execute("COMMIT")
            return True
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def record_paper_exit_event(self, intent_id: str, event: str, *, reason: str | None = None) -> None:
        from services.execution.paper_exit_retry import exit_identity
        con = _connect()
        try:
            stored = _fetch_intent_row(con, str(intent_id))
            if stored is None:
                raise ValueError("pending_exit_missing")
            exit_identity(_decode_intent_row(stored))
            con.execute("INSERT INTO paper_exit_events(intent_id,ts,event,reason) VALUES(?,?,?,?)",
                        (str(intent_id), _now(), str(event), reason))
        finally:
            con.close()

    def list_paper_exit_events(self, intent_id: str) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            return [dict(zip(("event_id","ts","event","reason"), r)) for r in con.execute(
                "SELECT event_id,ts,event,reason FROM paper_exit_events WHERE intent_id=? ORDER BY event_id",
                (str(intent_id),)).fetchall()]
        finally:
            con.close()

    def has_open_strategy_intent(self, symbol: str) -> bool:
        con = _connect()
        try:
            return con.execute(
                "SELECT 1 FROM trade_intents WHERE source='strategy' AND symbol=? "
                "AND status IN ('queued', 'submitting', 'submitted', 'held') LIMIT 1",
                (str(symbol),),
            ).fetchone() is not None
        finally:
            con.close()

    def strategy_sell_intents_after(self, symbol: str, after_rowid: int) -> List[Dict[str, Any]]:
        """Ordered written-sell evidence, including damaged metadata; no newest-row limit."""
        from storage.exit_event_journal import _decode_payload
        con = _connect()
        try:
            rows = con.execute(
                "SELECT rowid,intent_id,venue,symbol,strategy_id,meta FROM trade_intents "
                "WHERE source='strategy' AND side='sell' AND symbol=? AND rowid>? ORDER BY rowid",
                (str(symbol), int(after_rowid)),
            ).fetchall()
            result = []
            for row in rows:
                # Use the journal's strict finite-object decoder. In particular,
                # duplicate keys (including nested ones) are ambiguous evidence.
                meta = _decode_payload(row[5]) if row[5] else None
                result.append(dict(zip(("rowid", "intent_id", "venue", "symbol", "strategy_id"), row[:5]),
                                   meta=meta, meta_raw=row[5]))
            return result
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
                if str(item["side"]).strip().lower() == "buy":
                    con.execute(
                        "INSERT INTO paper_buy_events(intent_id,ts,event,status,reason) VALUES(?,?,?,?,?)",
                        (intent_id, now, "picked_up", "submitting", None),
                    )
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
            con.execute("BEGIN IMMEDIATE")
            nxt = normalize_live_queue_status(status)
            before = _fetch_intent_row(con, intent_id)
            now = _now()
            cur = con.execute(
                """
                UPDATE trade_intents
                   SET status=?, last_error=?, client_order_id=COALESCE(?, client_order_id), linked_order_id=COALESCE(?, linked_order_id), updated_ts=?
                 WHERE intent_id=?
                   AND status NOT IN ('filled', 'rejected', 'canceled', 'cancelled', 'error', 'expired')
                   AND (
                        status = ?
                     OR (lower(trim(side)) = 'buy' AND ? = 'expired' AND status IN ('queued','submitting','submitted','held'))
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
                    now,
                    str(intent_id),
                    nxt,
                    nxt,
                    nxt,
                    nxt,
                    nxt,
                    nxt,
                ),
            )
            if cur.rowcount == 1 and before and str(before[8]).strip().lower() == "buy" and (
                    before[12] != nxt or before[13] != last_error):
                con.execute(
                    "INSERT INTO paper_buy_events(intent_id,ts,event,status,reason) VALUES(?,?,?,?,?)",
                    (str(intent_id), now, "transition", nxt, last_error),
                )
            con.commit()
            return cur.rowcount == 1
        finally:
            con.close()

    def list_pending_paper_buys(self) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT intent_id,created_ts,ts,source,strategy_id,action,venue,symbol,side,order_type,qty,"
                "limit_price,status,last_error,client_order_id,linked_order_id,meta,updated_ts "
                "FROM trade_intents WHERE lower(trim(side))='buy' "
                "AND status IN ('queued','submitting','submitted','held') ORDER BY created_ts,intent_id"
            ).fetchall()
            return [_decode_intent_row(row) for row in rows]
        finally:
            con.close()

    def record_paper_buy_event(self, intent_id: str, event: str, *, reason: str | None = None) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT INTO paper_buy_events(intent_id,ts,event,status,reason) "
                "SELECT intent_id,?,?,status,? FROM trade_intents WHERE intent_id=? AND lower(trim(side))='buy'",
                (_now(), str(event), reason, str(intent_id)),
            )
        finally:
            con.close()

    def list_paper_buys_needing_alert(self) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT intent_id,created_ts,ts,source,strategy_id,action,venue,symbol,side,order_type,qty,"
                "limit_price,status,last_error,client_order_id,linked_order_id,meta,updated_ts "
                "FROM trade_intents t WHERE lower(trim(side))='buy' "
                "AND status IN ('expired','rejected','canceled','cancelled') "
                "AND EXISTS (SELECT 1 FROM paper_buy_events e WHERE e.intent_id=t.intent_id) "
                "AND NOT EXISTS (SELECT 1 FROM paper_buy_events e WHERE e.intent_id=t.intent_id "
                "AND e.event='alert_result' AND e.reason='external_channel_accepted') "
                "ORDER BY updated_ts,intent_id"
            ).fetchall()
            return [_decode_intent_row(row) for row in rows]
        finally:
            con.close()

    def list_paper_buy_events(self, intent_id: str) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            return [dict(zip(("event_id", "ts", "event", "status", "reason"), row)) for row in con.execute(
                "SELECT event_id,ts,event,status,reason FROM paper_buy_events WHERE intent_id=? ORDER BY event_id",
                (str(intent_id),),
            ).fetchall()]
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
