from __future__ import annotations
import json
import math
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from services.execution.intent_lifecycle import normalize_live_queue_status
from services.markets.math_utils import decimal_value
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
CREATE TABLE IF NOT EXISTS live_trade_intent_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  intent_id TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  pre_status TEXT,
  post_status TEXT NOT NULL,
  reason TEXT,
  last_error TEXT,
  client_order_id TEXT,
  exchange_order_id TEXT,
  source TEXT,
  meta TEXT
);
CREATE INDEX IF NOT EXISTS idx_ltie_intent_event ON live_trade_intent_events(intent_id, event_id);
CREATE INDEX IF NOT EXISTS idx_ltie_event_ts ON live_trade_intent_events(event_ts);
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


def _finite_real_input(value: Any, *, name: str, required: bool = True) -> float | None:
    if value is None:
        if required:
            raise ValueError(f"invalid_live_intent_numeric:{name}:missing")
        return None
    try:
        return float(decimal_value(value, name=name))
    except ValueError as exc:
        raise ValueError(f"invalid_live_intent_numeric:{name}:{exc}") from exc


def _event_meta_json(meta: dict[str, Any] | None) -> str | None:
    if meta is None:
        return None
    return json.dumps(dict(meta), sort_keys=True)


def _insert_intent_event(
    con: sqlite3.Connection,
    *,
    intent_id: str,
    actor: str,
    action: str,
    pre_status: str | None,
    post_status: str,
    reason: str | None = None,
    last_error: str | None = None,
    client_order_id: str | None = None,
    exchange_order_id: str | None = None,
    source: str | None = None,
    event_ts: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    con.execute(
        """
        INSERT INTO live_trade_intent_events(
          intent_id, event_ts, actor, action, pre_status, post_status, reason,
          last_error, client_order_id, exchange_order_id, source, meta
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            str(intent_id),
            str(event_ts or _now()),
            str(actor or "system"),
            str(action or "status_transition"),
            pre_status,
            str(post_status),
            reason,
            last_error,
            client_order_id,
            exchange_order_id,
            source,
            _event_meta_json(meta),
        ),
    )


class LiveIntentQueueSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert_intent(self, row: Dict[str, Any]) -> None:
        intent_id = str(row["intent_id"])
        meta_json = json.dumps(row.get("meta")) if row.get("meta") is not None else None
        now = _now()
        qty = _finite_real_input(row["qty"], name="qty")
        limit_price = _finite_real_input(row.get("limit_price"), name="limit_price", required=False)

        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute(
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
                    qty,
                    limit_price,
                    str(row["status"]),
                    row.get("last_error"),
                    row.get("client_order_id"),
                    row.get("exchange_order_id"),
                    meta_json,
                    now,
                ),
            )
            if cur.rowcount == 1:
                _insert_intent_event(
                    con,
                    intent_id=intent_id,
                    actor=str(row.get("source") or "system"),
                    action="insert",
                    pre_status=None,
                    post_status=str(row["status"]),
                    reason="upsert_intent_insert",
                    last_error=row.get("last_error"),
                    client_order_id=row.get("client_order_id"),
                    exchange_order_id=row.get("exchange_order_id"),
                    source=str(row.get("source") or ""),
                    event_ts=now,
                    meta={
                        "insert_only": True,
                        "venue": str(row["venue"]),
                        "symbol": str(row["symbol"]),
                        "strategy_id": row.get("strategy_id"),
                    },
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

    def list_intent_events(
        self,
        *,
        intent_id: str | None = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = (
                "SELECT event_id, intent_id, event_ts, actor, action, pre_status, "
                "post_status, reason, last_error, client_order_id, exchange_order_id, "
                "source, meta FROM live_trade_intent_events"
            )
            args: list[Any] = []
            if intent_id:
                q += " WHERE intent_id=?"
                args.append(str(intent_id))
            q += " ORDER BY event_id ASC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "event_id": r[0],
                    "intent_id": r[1],
                    "event_ts": r[2],
                    "actor": r[3],
                    "action": r[4],
                    "pre_status": r[5],
                    "post_status": r[6],
                    "reason": r[7],
                    "last_error": r[8],
                    "client_order_id": r[9],
                    "exchange_order_id": r[10],
                    "source": r[11],
                    "meta": json.loads(r[12]) if r[12] else None,
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

    def claim_next_queued(self, limit: int = 20) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            rows = con.execute(
                ("SELECT intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, exchange_order_id, meta, updated_ts "
                 "FROM live_trade_intents WHERE status='queued' ORDER BY created_ts ASC LIMIT ?"),
                (int(limit),),
            ).fetchall()

            claimed = []
            now = _now()
            for r in rows:
                intent_id = str(r[0])
                client_order_id = str(r[13] or f"live_intent_{intent_id}")
                cur = con.execute(
                    """
                    UPDATE live_trade_intents
                       SET status='submitting', client_order_id=?, updated_ts=?
                     WHERE intent_id=?
                       AND status='queued'
                    """,
                    (client_order_id, now, intent_id),
                )
                if cur.rowcount != 1:
                    continue
                _insert_intent_event(
                    con,
                    intent_id=intent_id,
                    actor="intent_consumer",
                    action="claim_next_queued",
                    pre_status="queued",
                    post_status="submitting",
                    reason="claim_next_queued",
                    last_error=r[12],
                    client_order_id=client_order_id,
                    exchange_order_id=r[14],
                    source=r[3],
                    event_ts=now,
                    meta={"limit": int(limit)},
                )
                claimed.append((
                    r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
                    r[8], r[9], r[10], "submitting", r[12], client_order_id,
                    r[14], r[15], now,
                ))

            con.execute("COMMIT")
            return [
                {
                    "intent_id": r[0], "created_ts": r[1], "ts": r[2], "source": r[3], "strategy_id": r[4], "venue": r[5], "symbol": r[6],
                    "side": r[7], "order_type": r[8], "qty": r[9], "limit_price": r[10], "status": r[11],
                    "last_error": r[12], "client_order_id": r[13], "exchange_order_id": r[14],
                    "meta": json.loads(r[15]) if r[15] else None, "updated_ts": r[16],
                }
                for r in claimed
            ]
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            con.close()

    def update_status(
        self,
        intent_id: str,
        status: str,
        *,
        last_error: str | None = None,
        client_order_id: str | None = None,
        exchange_order_id: str | None = None,
    ) -> bool:
        con = _connect()
        try:
            nxt = normalize_live_queue_status(status)
            now = _now()
            con.execute("BEGIN IMMEDIATE")
            current = con.execute(
                """
                SELECT status, last_error, client_order_id, exchange_order_id, source
                  FROM live_trade_intents
                 WHERE intent_id=?
                """,
                (str(intent_id),),
            ).fetchone()
            cur = con.execute(
                """
                UPDATE live_trade_intents
                   SET status=?, last_error=?, client_order_id=COALESCE(?, client_order_id), exchange_order_id=COALESCE(?, exchange_order_id), updated_ts=?
                 WHERE intent_id=?
                   AND status NOT IN ('filled', 'rejected', 'canceled', 'cancelled', 'error', 'expired')
                   AND (
                        status = ?
                     OR (status = 'queued' AND ? IN ('submitting', 'submitted', 'rejected', 'held', 'submit_unknown', 'expired'))
                     OR (status = 'submitting' AND ? IN ('submitted', 'rejected', 'submit_unknown', 'expired'))
                     OR (status = 'submitted' AND ? IN ('filled', 'canceled', 'cancelled', 'rejected', 'error', 'held'))
                     OR (status = 'submit_unknown' AND ? IN ('submitted', 'rejected', 'error'))
                     OR (status = 'held' AND ? IN ('queued', 'rejected'))
                   )
                """,
                (
                    str(nxt),
                    last_error,
                    client_order_id,
                    exchange_order_id,
                    now,
                    str(intent_id),
                    str(nxt),
                    str(nxt),
                    str(nxt),
                    str(nxt),
                    str(nxt),
                    str(nxt),
                ),
            )
            if cur.rowcount != 1:
                con.execute("COMMIT")
                return False
            _insert_intent_event(
                con,
                intent_id=str(intent_id),
                actor="queue_status_writer",
                action="update_status",
                pre_status=str(current[0]) if current else None,
                post_status=str(nxt),
                reason="update_status",
                last_error=last_error,
                client_order_id=client_order_id
                or (str(current[2]) if current and current[2] else None),
                exchange_order_id=exchange_order_id
                or (str(current[3]) if current and current[3] else None),
                source=str(current[4]) if current and current[4] else None,
                event_ts=now,
            )
            con.execute("COMMIT")
            return True
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            raise
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
        try:
            max_trades_f = float(max_trades)
            max_notional_d = decimal_value(max_notional, name="max_notional")
        except Exception:
            return False, "risk:invalid_cap"
        if not math.isfinite(max_trades_f):
            return False, "risk:invalid_cap"
        try:
            notional_est_d = decimal_value(notional_est, name="notional_est")
        except Exception:
            return False, "risk:invalid_notional_est"
        if notional_est_d < 0:
            return False, "risk:invalid_notional_est"

        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            def _get(k: str) -> str:
                r = con.execute(
                    "SELECT v FROM live_consumer_state WHERE k=?", (k,)
                ).fetchone()
                return r[0] if r else "0"
            try:
                trades = int(float(_get("risk:trades")))
                notional_d = decimal_value(_get("risk:notional"), name="risk_notional")
            except Exception:
                con.execute("ROLLBACK")
                return False, "risk:corrupt_state"
            if trades < 0 or notional_d < 0:
                con.execute("ROLLBACK")
                return False, "risk:corrupt_state"
            if max_trades_f > 0 and trades >= int(max_trades_f):
                con.execute("ROLLBACK")
                return False, "risk:max_trades_per_day"
            if max_notional_d > 0 and notional_d + notional_est_d > max_notional_d:
                con.execute("ROLLBACK")
                return False, "risk:max_daily_notional_quote"
            con.execute(
                "INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)",
                ("risk:trades", str(trades + 1)),
            )
            con.execute(
                "INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)",
                ("risk:notional", str(notional_d + notional_est_d)),
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

    def reset_risk_state_for_day(self, day: str) -> None:
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)",
                ("risk:day", str(day)),
            )
            con.execute(
                "INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)",
                ("risk:trades", "0"),
            )
            con.execute(
                "INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)",
                ("risk:notional", "0.0"),
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

    def set_state(self, k: str, v: str) -> None:
        key = str(k)
        if key in {"risk:day", "risk:trades", "risk:notional"}:
            raise ValueError(f"reserved live risk state key: {key}")
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES(?,?)", (key, str(v)))
            con.commit()
        finally:
            con.close()
