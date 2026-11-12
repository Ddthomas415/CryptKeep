from __future__ import annotations
import sqlite3
import json
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from urllib.parse import quote
from services.execution.intent_ttl import _parse_created_epoch
from services.execution.paper_buy_policy import PAPER_BUY_CREATED_TS, buy_age_verdict
from services.os.app_paths import data_dir
from storage.exit_event_journal import _decode_payload

DB_PATH = data_dir() / "paper_trading.sqlite"
FLOAT_CASH_EPSILON = 1e-9
PAPER_EXIT_POLICY = "retry_until_filled_v1"

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
  reject_reason TEXT,
  strategy_id TEXT,
  meta_json TEXT
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


def _paper_buy_now(clock: Callable[[], Any] | None) -> Any:
    try:
        return datetime.now(timezone.utc) if clock is None else clock()
    except Exception:
        return None


def _paper_buy_queue_origins(client_order_id: str) -> tuple[list[Any], str | None]:
    """Read only queue creation evidence; absence is inconclusive for intent clients."""
    canonical = client_order_id.startswith("paper_intent_")
    queue_path = DB_PATH.parent / "intent_queue.sqlite"
    try:
        queue_path.stat()
    except FileNotFoundError:
        return [], "paper_buy_queue_origin_missing" if canonical else None
    except OSError:
        return [], "paper_buy_queue_origin_unreadable"
    con = None
    try:
        uri = "file:" + quote(str(queue_path.absolute()), safe="/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=0.25)
        sql = "SELECT created_ts FROM trade_intents WHERE client_order_id=?"
        args = [client_order_id]
        if canonical:
            sql += " OR intent_id=?"
            args.append(client_order_id[len("paper_intent_"):])
        origins = [row[0] for row in con.execute(sql, args).fetchall()]
        if not origins and canonical:
            return [], "paper_buy_queue_origin_missing"
        return origins, None
    except (sqlite3.Error, OSError, ValueError):
        return [], "paper_buy_queue_origin_unreadable"
    finally:
        if con is not None:
            con.close()


def _paper_buy_age_verdict(created_ts, meta_json, now_ts, queue_created_ts=None, *, queue_origins=()) -> dict:
    if meta_json is None or (isinstance(meta_json, str) and meta_json.strip() == "null"):
        meta = None
    else:
        meta = _decode_payload(meta_json)
        if meta is None:
            return {"ok": False, "reason": "invalid_stored_order_meta", "age_s": None, "created_ts": None}
    origin = meta[PAPER_BUY_CREATED_TS] if isinstance(meta, dict) and PAPER_BUY_CREATED_TS in meta else created_ts
    verdicts = [{**buy_age_verdict(origin, now_ts), "created_ts": origin}]
    if queue_created_ts is not None:
        verdicts.append({**buy_age_verdict(queue_created_ts, now_ts), "created_ts": queue_created_ts})
    verdicts.extend({**buy_age_verdict(value, now_ts), "created_ts": value} for value in queue_origins)
    # Invalid/future evidence cannot be hidden by a valid alternative origin.
    for verdict in verdicts:
        if not verdict["ok"] and verdict["reason"] != "paper_buy_ttl:expired":
            return verdict
    return max(verdicts, key=lambda verdict: verdict["age_s"])


def _paper_fill_id(order_id: Any, price: Any, qty: Any) -> str:
    return f"paper:{str(order_id)}:{float(price):.12f}:{float(qty):.12f}"

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)

    cols = [r[1] for r in con.execute("PRAGMA table_info(paper_orders)").fetchall()]
    if "strategy_id" not in cols:
        con.execute("ALTER TABLE paper_orders ADD COLUMN strategy_id TEXT")
    if "meta_json" not in cols:
        con.execute("ALTER TABLE paper_orders ADD COLUMN meta_json TEXT")
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

    def _get_state_conn(self, con: sqlite3.Connection, k: str) -> Optional[str]:
        r = con.execute("SELECT v FROM paper_state WHERE k=?", (str(k),)).fetchone()
        return r[0] if r else None

    def _set_state_conn(self, con: sqlite3.Connection, k: str, v: str) -> None:
        con.execute("INSERT OR REPLACE INTO paper_state(k,v) VALUES(?,?)", (str(k), str(v)))

    def initialize_account(self, starting_cash_quote: Any, quote_currency: str) -> dict:
        """Initialize defaults atomically; certify an origin only for a fresh ledger."""
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            cash = self._get_state_conn(con, "cash_quote")
            realized = self._get_state_conn(con, "realized_pnl")
            try:
                realized_zero = realized is None or Decimal(realized).is_zero()
            except InvalidOperation:
                realized_zero = False
            fresh = (cash is None and realized_zero
                     and self._get_state_conn(con, "paper_account_origin_v1") is None
                     and not any(con.execute("SELECT 1 FROM " + table + " LIMIT 1").fetchone()
                                 for table in ("paper_orders", "paper_fills", "paper_positions")))
            if cash is None:
                try:
                    starting_cash = float(starting_cash_quote)
                except (TypeError, ValueError, OverflowError) as exc:
                    raise ValueError("invalid_starting_cash_quote") from exc
                if isinstance(starting_cash_quote, bool) or not math.isfinite(starting_cash) or starting_cash <= 0:
                    raise ValueError("invalid_starting_cash_quote")
            if fresh:
                if (not isinstance(quote_currency, str) or not quote_currency.strip().isascii()
                        or not quote_currency.strip().isalnum()):
                    raise ValueError("invalid_quote_currency")
                currency = quote_currency.strip().upper()
            if cash is None:
                self._set_state_conn(con, "cash_quote", str(starting_cash))
            if realized is None:
                self._set_state_conn(con, "realized_pnl", "0.0")
            if fresh:
                self._set_state_conn(con, "paper_account_origin_v1", json.dumps({
                    "schema": 1, "cash_quote": starting_cash, "quote_currency": currency,
                }, sort_keys=True, allow_nan=False))
            con.execute("COMMIT")
            return {"baseline_created": fresh}
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def account_reconciliation_snapshot(self) -> dict:
        """Read whitelisted account evidence while ledger writes are frozen."""
        con = _connect()
        queue = None
        try:
            con.execute("BEGIN IMMEDIATE")
            uri = "file:" + quote(str((DB_PATH.parent / "intent_queue.sqlite").absolute()), safe="/") + "?mode=ro"
            queue = sqlite3.connect(uri, uri=True, timeout=0.25, isolation_level=None)
            con.row_factory = sqlite3.Row
            queue.row_factory = sqlite3.Row
            queue.execute("BEGIN")
            intents = [dict(row) for row in queue.execute(
                "SELECT intent_id,created_ts,updated_ts,source,venue,symbol,side,order_type,qty,status,"
                "client_order_id,linked_order_id FROM trade_intents ORDER BY intent_id")]
            event_ids = [row[0] for row in queue.execute(
                "SELECT intent_id FROM paper_buy_events UNION SELECT intent_id FROM paper_exit_events "
                "ORDER BY intent_id")]
            orders = [dict(row) for row in con.execute(
                "SELECT order_id,client_order_id,created_ts,ts,venue,symbol,side,order_type,qty,limit_price,"
                "status,reject_reason,strategy_id FROM paper_orders ORDER BY rowid")]
            fills = [dict(row) for row in con.execute("SELECT rowid AS sequence,* FROM paper_fills ORDER BY rowid")]
            positions = [dict(row) for row in con.execute("SELECT * FROM paper_positions ORDER BY symbol")]
            state = {row[0]: row[1] for row in con.execute(
                "SELECT k,v FROM paper_state WHERE k IN "
                "('cash_quote','realized_pnl','paper_account_origin_v1','paper_watchdog_seen_v1')")}
            queue.execute("COMMIT")
            con.execute("COMMIT")
            return dict(orders=orders, fills=fills, positions=positions, intents=intents,
                        event_intent_ids=event_ids, state=state)
        except Exception:
            try:
                if queue is not None:
                    queue.rollback()
            finally:
                con.rollback()
            raise
        finally:
            try:
                if queue is not None:
                    queue.close()
            finally:
                con.close()

    def record_account_reconciliation_seen(self, intent_ids: list[str]) -> list[str]:
        """Atomically retain the union; damaged prior evidence is never replaced."""
        def valid_ids(value):
            return isinstance(value, list) and all(
                isinstance(item, str) and item and item == item.strip() for item in value)

        if not valid_ids(intent_ids):
            raise ValueError("invalid_account_reconciliation_intent_ids")
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            raw = self._get_state_conn(con, "paper_watchdog_seen_v1")
            try:
                previous = [] if raw is None else json.loads(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid_paper_watchdog_seen") from exc
            if not valid_ids(previous):
                raise ValueError("invalid_paper_watchdog_seen")
            merged = sorted(set(previous).union(intent_ids))
            self._set_state_conn(con, "paper_watchdog_seen_v1", json.dumps(merged))
            con.execute("COMMIT")
            return merged
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def _exit_number(value: Any, *, positive: bool = True) -> bool:
        try:
            return (isinstance(value, (int, float)) and not isinstance(value, bool)
                    and math.isfinite(value) and (value > 0 if positive else value >= 0))
        except OverflowError:
            return False

    @classmethod
    def _exit_identity(cls, row: dict) -> dict | None:
        meta = row.get("meta")
        if not isinstance(meta, dict) or meta.get("paper_exit_policy") != PAPER_EXIT_POLICY:
            return None
        exit_id = meta.get("paper_exit_id")
        if not isinstance(exit_id, str) or not exit_id or exit_id != exit_id.strip():
            return None
        if row.get("client_order_id") != "paper_intent_" + exit_id or row.get("side") != "sell":
            return None
        for field in ("venue", "symbol"):
            value = row.get(field)
            if not isinstance(value, str) or not value or value != value.strip():
                return None
        if not isinstance(row.get("order_type"), str) or row["order_type"] not in {"market", "limit"}:
            return None
        limit = row.get("limit_price")
        if limit is not None and not cls._exit_number(limit):
            return None
        if row["order_type"] == "limit" and limit is None:
            return None
        strategy = row.get("strategy_id")
        if strategy is not None and (not isinstance(strategy, str) or not strategy.strip()):
            return None
        return {**{key: row.get(key) for key in (
            "client_order_id", "venue", "symbol", "side", "order_type", "limit_price", "strategy_id",
        )}, "paper_exit_id": exit_id, "paper_exit_policy": PAPER_EXIT_POLICY}

    @staticmethod
    def _exit_order_conn(con: sqlite3.Connection, *, client_order_id: str) -> dict | None:
        cur = con.execute("SELECT * FROM paper_orders WHERE client_order_id=?", (client_order_id,))
        raw = cur.fetchone()
        if raw is None:
            return None
        row = dict(zip((col[0] for col in cur.description), raw))
        try:
            row["meta"] = json.loads(row.pop("meta_json") or "null")
        except (TypeError, ValueError):
            row["meta"] = None
        return row

    def _exit_terminal_conn(self, con: sqlite3.Connection, identity: dict) -> dict | None:
        raw = self._get_state_conn(con, "paper_exit_terminal:" + identity["paper_exit_id"])
        if raw is None:
            return None
        try:
            terminal = json.loads(raw)
            if (not isinstance(terminal, dict) or terminal.get("identity") != identity
                    or terminal.get("state") not in {"filled", "superseded"}):
                raise ValueError("invalid terminal")
            return terminal
        except (TypeError, ValueError):
            return {"state": "blocked", "reason": "invalid_exit_terminal"}

    def _write_exit_terminal_conn(self, con: sqlite3.Connection, identity: dict, state: str, **extra) -> None:
        self._set_state_conn(
            con, "paper_exit_terminal:" + identity["paper_exit_id"],
            json.dumps({"identity": identity, "state": state, **extra}, sort_keys=True, allow_nan=False),
        )

    def _supersede_exit_conn(self, con: sqlite3.Connection, identity: dict, existing: dict | None) -> dict:
        self._write_exit_terminal_conn(con, identity, "superseded", qty=0.0)
        if existing is not None and existing["status"] != "filled":
            self._update_order_status_conn(con, existing["order_id"], "superseded", "zero_holding")
            existing.update(status="superseded", reject_reason="zero_holding")
        return {"state": "superseded", "qty": 0.0, "reason": "zero_holding", "order": existing}

    @classmethod
    def _exit_fills_conn(cls, con: sqlite3.Connection, identity: dict) -> list[dict]:
        # Include noncanonical legacy/corrupt rows sharing the root, not just the unique client ID.
        rows = con.execute(
            "SELECT f.fill_id, f.order_id, f.price, f.qty, f.fee FROM paper_fills f "
            "JOIN paper_orders o ON o.order_id=f.order_id WHERE o.client_order_id=? OR "
            "CASE WHEN json_valid(o.meta_json) THEN json_extract(o.meta_json, '$.paper_exit_id') END=?",
            (identity["client_order_id"], identity["paper_exit_id"]),
        ).fetchall()
        return [dict(zip(("fill_id", "order_id", "price", "qty", "fee"), row)) for row in rows]

    @classmethod
    def _valid_exit_fill(cls, fills: list[dict], existing: dict | None) -> bool:
        return (existing is not None and len(fills) == 1
                and fills[0]["order_id"] == existing["order_id"]
                and cls._exit_number(fills[0]["price"])
                and cls._exit_number(fills[0]["qty"])
                and cls._exit_number(fills[0]["fee"], positive=False)
                and fills[0]["qty"] <= existing["qty"])

    def prepare_paper_exit(
        self, *, client_order_id, exit_id, venue, symbol, order_type, qty,
        limit_price, strategy_id, meta, activate=False,
    ) -> dict:
        requested = dict(client_order_id=client_order_id, venue=venue, symbol=symbol, side="sell",
                         order_type=order_type, qty=qty, limit_price=limit_price,
                         strategy_id=strategy_id, meta=meta)
        identity = self._exit_identity(requested)
        blocked = {"state": "blocked", "qty": 0.0}
        if (identity is None or identity["paper_exit_id"] != exit_id
                or not self._exit_number(qty) or not isinstance(activate, bool)):
            return {**blocked, "reason": "invalid_exit_request"}
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            existing = self._exit_order_conn(con, client_order_id=client_order_id)
            result = {**blocked, "reason": "exit_identity_mismatch", "order": existing}
            if existing is not None and (self._exit_identity(existing) != identity
                                        or not self._exit_number(existing["qty"])):
                con.execute("COMMIT")
                return result
            terminal = self._exit_terminal_conn(con, identity)
            fills = self._exit_fills_conn(con, identity)
            if terminal and terminal["state"] == "blocked":
                result = {**blocked, "reason": terminal["reason"], "order": existing}
            elif terminal and terminal["state"] == "superseded":
                if fills or (existing and existing["status"] == "filled"):
                    result = {**blocked, "reason": "exit_terminal_conflict", "order": existing}
                else:
                    result = self._supersede_exit_conn(con, identity, existing)
            elif existing and existing["status"] == "filled":
                if self._valid_exit_fill(fills, existing) and (
                    not terminal or terminal.get("fill_id") == fills[0]["fill_id"]
                ):
                    result = {"state": "filled", "qty": fills[0]["qty"], "order": existing,
                              "reason": "durable_fill"}
                else:
                    result = {**blocked, "reason": "missing_or_conflicting_fill", "order": existing}
            elif fills or terminal:
                result = {**blocked, "reason": "exit_fill_state_conflict", "order": existing}
            elif existing and existing["status"] not in {"new", "rejected", "superseded"}:
                result = {**blocked, "reason": "unsupported_exit_status", "order": existing}
            else:
                pos = self._get_position_conn(con, symbol)
                held = pos["qty"] if pos else 0.0
                if not self._exit_number(held, positive=False):
                    result = {**blocked, "reason": "invalid_holding", "order": existing}
                elif held == 0 or (existing and existing["status"] == "superseded"):
                    result = self._supersede_exit_conn(con, identity, existing)
                else:
                    bounded = min(qty, held, existing["qty"] if existing else qty)
                    if existing and activate:
                        con.execute("UPDATE paper_orders SET qty=?, status='new', reject_reason=NULL "
                                    "WHERE order_id=?", (bounded, existing["order_id"]))
                        existing.update(qty=bounded, status="new", reject_reason=None)
                    result = {"state": "ready", "qty": bounded, "order": existing,
                              "reason": "activated" if activate else "validated"}
            con.execute("COMMIT")
            return result
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def insert_order(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO paper_orders(order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason, strategy_id, meta_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
                    row.get("strategy_id"),
                    json.dumps(row.get("meta")) if row.get("meta") is not None else None,
                ),
            )
        finally:
            con.close()

    def get_order_by_client_id(self, client_order_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason, strategy_id, meta_json "
                "FROM paper_orders WHERE client_order_id=?",
                (str(client_order_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "order_id": r[0], "client_order_id": r[1], "created_ts": r[2], "ts": r[3],
                "venue": r[4], "symbol": r[5], "side": r[6], "order_type": r[7],
                "qty": r[8], "limit_price": r[9], "status": r[10], "reject_reason": r[11],
                "strategy_id": r[12], "meta": json.loads(r[13]) if r[13] else None,
            }
        finally:
            con.close()

    def update_order_status(self, order_id: str, status: str, reject_reason: str | None = None) -> None:
        con = _connect()
        try:
            con.execute("UPDATE paper_orders SET status=?, reject_reason=? WHERE order_id=?", (str(status), reject_reason, str(order_id)))
        finally:
            con.close()

    def _update_order_status_conn(self, con: sqlite3.Connection, order_id: str, status: str, reject_reason: str | None = None) -> None:
        con.execute(
            "UPDATE paper_orders SET status=?, reject_reason=? WHERE order_id=?",
            (str(status), reject_reason, str(order_id)),
        )

    def _paper_buy_terminal_conn(self, con: sqlite3.Connection, client_order_id: str) -> dict | None:
        raw = self._get_state_conn(con, "paper_buy_terminal:" + client_order_id)
        if raw is None:
            return None
        terminal = _decode_payload(raw)
        if (terminal is None or terminal.get("client_order_id") != client_order_id
                or not isinstance(terminal.get("state"), str)
                or terminal["state"] not in {"expired", "rejected"}
                or not isinstance(terminal.get("reason"), str) or not terminal["reason"]):
            return {"state": "rejected", "reason": "invalid_buy_terminal"}
        return terminal

    def _write_paper_buy_terminal_conn(
        self, con: sqlite3.Connection, client_order_id: str, state: str, reason: str, created_ts: Any,
    ) -> None:
        self._set_state_conn(con, "paper_buy_terminal:" + client_order_id, json.dumps({
            "client_order_id": client_order_id, "state": state, "reason": reason,
            "created_ts": str(created_ts) if created_ts is not None else None,
        }, sort_keys=True, allow_nan=False))

    @classmethod
    def _paper_buy_order_matches(cls, existing: dict, expected: dict) -> bool:
        if not isinstance(expected, dict):
            return False
        for key in ("venue", "symbol", "side", "order_type"):
            left, right = existing.get(key), expected.get(key)
            if not isinstance(left, str) or not isinstance(right, str):
                return False
            left, right = left.strip(), right.strip()
            if key != "symbol":
                left, right = left.lower(), right.lower()
            if not left or left != right or (key == "side" and left != "buy"):
                return False
        if (not cls._exit_number(existing.get("qty")) or not cls._exit_number(expected.get("qty"))
                or existing["qty"] != expected["qty"]):
            return False
        left, right = existing.get("limit_price"), expected.get("limit_price")
        if left is not None and not cls._exit_number(left):
            return False
        if right is not None and not cls._exit_number(right):
            return False
        linked = expected.get("linked_order_id")
        return left == right and (linked is None or linked == existing["order_id"])

    def expire_buy_order(
        self, client_order_id: str, *, created_ts: Any = None,
        clock: Callable[[], Any] | None = None,
        fence_missing: bool = False, expected_order: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fence buys atomically, retaining queue age and optional missing-order expiry."""
        client_order_id = str(client_order_id)
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute("SELECT * FROM paper_orders WHERE client_order_id=?", (str(client_order_id),))
            raw = cur.fetchone()
            if raw is None:
                terminal = self._paper_buy_terminal_conn(con, client_order_id)
                if terminal is not None:
                    con.execute("COMMIT")
                    return {"state": terminal["state"], "reason": terminal["reason"], "order": None}
                if fence_missing:
                    verdict = buy_age_verdict(created_ts, _paper_buy_now(clock))
                    if not verdict["ok"]:
                        reason = verdict["reason"]
                        state = "expired" if reason == "paper_buy_ttl:expired" else "rejected"
                        self._write_paper_buy_terminal_conn(con, client_order_id, state, reason, created_ts)
                        con.execute("COMMIT")
                        return {"state": state, "reason": reason, "order": None}
                con.execute("COMMIT")
                return {"state": "missing", "order": None, "reason": "order_not_found"}
            existing = dict(zip((col[0] for col in cur.description), raw))
            meta_json = existing.pop("meta_json")
            existing["meta"] = _decode_payload(meta_json) if meta_json is not None else None
            if expected_order is not None and not self._paper_buy_order_matches(existing, expected_order):
                con.execute("COMMIT")
                return {"state": "blocked", "reason": "paper_buy_order_identity_mismatch", "order": existing}
            state = str(existing["status"]).strip().lower()
            reason = existing.get("reject_reason") or state
            if str(existing["side"]).strip().lower() == "buy" and state in {"new", "open"}:
                terminal = self._paper_buy_terminal_conn(con, client_order_id)
                if terminal is not None:
                    state, reason = terminal["state"], terminal["reason"]
                    self._update_order_status_conn(con, existing["order_id"], state, reason)
                    existing.update(status=state, reject_reason=reason)
                    con.execute("COMMIT")
                    return {"state": state, "reason": reason, "order": existing}
                queue_origins, lookup_error = _paper_buy_queue_origins(client_order_id)
                if lookup_error is not None:
                    con.execute("COMMIT")
                    return {"state": "blocked", "reason": lookup_error, "order": existing}
                now_ts = _paper_buy_now(clock)
                verdict = _paper_buy_age_verdict(
                    existing["created_ts"], meta_json, now_ts, created_ts, queue_origins=queue_origins,
                )
                reason = verdict["reason"]
                meta = existing["meta"]
                origin = meta[PAPER_BUY_CREATED_TS] if isinstance(meta, dict) and PAPER_BUY_CREATED_TS in meta else existing["created_ts"]
                if not verdict["ok"]:
                    state = "expired" if reason == "paper_buy_ttl:expired" else "rejected"
                    self._update_order_status_conn(con, existing["order_id"], state, reason)
                    self._write_paper_buy_terminal_conn(
                        con, client_order_id, state, reason, verdict["created_ts"],
                    )
                    existing.update(status=state, reject_reason=reason)
                elif _parse_created_epoch(verdict["created_ts"]) < _parse_created_epoch(origin):
                    # Only shorten the authoritative lifetime; preserve all other metadata.
                    meta = {**(meta or {}), PAPER_BUY_CREATED_TS: datetime.fromtimestamp(
                        _parse_created_epoch(verdict["created_ts"]), timezone.utc).isoformat()}
                    con.execute("UPDATE paper_orders SET meta_json=? WHERE order_id=?",
                                (json.dumps(meta, allow_nan=False), existing["order_id"]))
                    existing["meta"] = meta
            con.execute("COMMIT")
            return {"state": state, "order": existing, "reason": reason}
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def list_orders(self, limit: int = 500, status: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason, strategy_id, meta_json "
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
                    "strategy_id": r[12], "meta": json.loads(r[13]) if r[13] else None,
                }
                for r in rows
            ]
        finally:
            con.close()

    def insert_fill(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO paper_fills(fill_id, order_id, ts, price, qty, fee, fee_currency) VALUES(?,?,?,?,?,?,?)",
                (str(row["fill_id"]), str(row["order_id"]), str(row["ts"]), float(row["price"]), float(row["qty"]), float(row["fee"]), str(row["fee_currency"])),
            )
        finally:
            con.close()

    def _insert_fill_conn(self, con: sqlite3.Connection, row: Dict[str, Any]) -> int:
        cur = con.execute(
            "INSERT OR IGNORE INTO paper_fills(fill_id, order_id, ts, price, qty, fee, fee_currency) VALUES(?,?,?,?,?,?,?)",
            (
                str(row["fill_id"]),
                str(row["order_id"]),
                str(row["ts"]),
                float(row["price"]),
                float(row["qty"]),
                float(row["fee"]),
                str(row["fee_currency"]),
            ),
        )
        return int(cur.rowcount or 0)

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

    def _upsert_position_conn(self, con: sqlite3.Connection, symbol: str, qty: float, avg_price: float, realized_pnl: float, *, updated_ts: str) -> None:
        con.execute(
            "INSERT OR REPLACE INTO paper_positions(symbol, qty, avg_price, realized_pnl, updated_ts) VALUES(?,?,?,?,?)",
            (str(symbol), float(qty), float(avg_price), float(realized_pnl), str(updated_ts)),
        )

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute("SELECT symbol, qty, avg_price, realized_pnl, updated_ts FROM paper_positions WHERE symbol=?", (str(symbol),)).fetchone()
            if not r:
                return None
            return {"symbol": r[0], "qty": r[1], "avg_price": r[2], "realized_pnl": r[3], "updated_ts": r[4]}
        finally:
            con.close()

    def _get_position_conn(self, con: sqlite3.Connection, symbol: str) -> Optional[Dict[str, Any]]:
        r = con.execute(
            "SELECT symbol, qty, avg_price, realized_pnl, updated_ts FROM paper_positions WHERE symbol=?",
            (str(symbol),),
        ).fetchone()
        if not r:
            return None
        return {"symbol": r[0], "qty": r[1], "avg_price": r[2], "realized_pnl": r[3], "updated_ts": r[4]}

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

    @classmethod
    def _committed_fill_receipt_conn(cls, con, order_id, order_qty):
        rows = con.execute(
            "SELECT fill_id, price, qty, fee FROM paper_fills WHERE order_id=? LIMIT 2",
            (order_id,),
        ).fetchall()
        if len(rows) == 1:
            fill_id, price, qty, fee = rows[0]
            if (fill_id and cls._exit_number(price) and cls._exit_number(qty)
                    and cls._exit_number(order_qty) and qty <= order_qty
                    and cls._exit_number(fee, positive=False)):
                return {"ok": True, "fill_id": fill_id, "price": price, "qty": qty,
                        "fee": fee, "idempotent": True}
        return {"ok": False, "reason": "missing_or_conflicting_fill", "unresolved": True}

    def apply_fill(
        self,
        *,
        order: Dict[str, Any],
        ts: str,
        price: float,
        qty: float,
        fee: float,
        fee_currency: str,
        execution_identity_evidence: Optional[Dict[str, Any]] = None,
        clock: Callable[[], Any] | None = None,
        hourly_candle_guard: Any = False,
        snapshot_quote_guard: Any = False,
        snapshot_quote: Optional[Dict[str, Any]] = None,
        snapshot_slippage_bps: Any = None,
    ) -> Dict[str, Any]:
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            order_row = con.execute(
                "SELECT order_id, symbol, side, status, reject_reason, client_order_id, meta_json, created_ts, venue, "
                "order_type, limit_price, qty "
                "FROM paper_orders WHERE order_id=?",
                (str(order["order_id"]),),
            ).fetchone()
            if not order_row:
                con.execute("ROLLBACK")
                return {"ok": False, "reason": "order_not_found"}

            order_id = str(order_row[0])
            symbol = str(order_row[1])
            side = str(order_row[2]).strip().lower()
            status = str(order_row[3]).strip().lower()
            if side == "buy":
                # A late retry must not reclassify an already committed fill.
                if status == "filled":
                    if snapshot_quote_guard is not False:
                        receipt = self._committed_fill_receipt_conn(con, order_id, order_row[11])
                    else:
                        receipt = {"ok": True, "fill_id": _paper_fill_id(order_id, price, qty),
                                   "fee": float(fee), "idempotent": True}
                    con.execute("COMMIT")
                    return receipt
                if status not in {"new", "open"}:
                    con.execute("COMMIT")
                    return {"ok": False, "reason": status}
                client_id = str(order_row[5])
                terminal = self._paper_buy_terminal_conn(con, client_id)
                if terminal is not None:
                    self._update_order_status_conn(con, order_id, terminal["state"], terminal["reason"])
                    con.execute("COMMIT")
                    return {"ok": False, "reason": terminal["reason"]}
                queue_origins, lookup_error = _paper_buy_queue_origins(client_id)
                if lookup_error is not None:
                    con.execute("COMMIT")
                    return {"ok": False, "reason": lookup_error}
                candle_quality = None
                if hourly_candle_guard is not False:
                    candle_quality = {"ok": False, "reason": "invalid_policy"}
                    if hourly_candle_guard is True:
                        try:
                            from services.market_data.hourly_candle_quality import check_cached_hourly_candles
                            candle_quality = check_cached_hourly_candles(
                                str(order_row[8]), symbol, clock=lambda: _paper_buy_now(clock), data_root=DB_PATH.parent,
                            )
                        except Exception:
                            candle_quality = {"ok": False, "reason": "cache_unreadable"}
                    if (not isinstance(candle_quality, dict) or type(candle_quality.get("ok")) is not bool
                            or not isinstance(candle_quality.get("reason"), str) or not candle_quality["reason"]):
                        candle_quality = {"ok": False, "reason": "invalid_verdict"}
                now_ts = _paper_buy_now(clock)
                verdict = _paper_buy_age_verdict(order_row[7], order_row[6], now_ts, queue_origins=queue_origins)
                if not verdict["ok"]:
                    reason = verdict["reason"]
                    state = "expired" if reason == "paper_buy_ttl:expired" else "rejected"
                    self._update_order_status_conn(con, order_id, state, reason)
                    self._write_paper_buy_terminal_conn(con, client_id, state, reason, verdict["created_ts"])
                    con.execute("COMMIT")
                    return {"ok": False, "reason": reason}
                if candle_quality is not None:
                    try:
                        diagnostic = json.dumps(candle_quality, sort_keys=True, allow_nan=False)
                        if _decode_payload(diagnostic) is None:
                            raise ValueError("invalid_candle_diagnostic")
                        self._set_state_conn(con, "paper_candle_check:" + order_id, diagnostic)
                    except Exception:
                        con.rollback()
                        return {"ok": False, "reason": "candle_data:evidence_unwritable", "unresolved": True}
                    now_ts = _paper_buy_now(clock)
                    verdict = _paper_buy_age_verdict(order_row[7], order_row[6], now_ts, queue_origins=queue_origins)
                    if not verdict["ok"]:
                        reason = verdict["reason"]
                        state = "expired" if reason == "paper_buy_ttl:expired" else "rejected"
                        self._update_order_status_conn(con, order_id, state, reason)
                        self._write_paper_buy_terminal_conn(con, client_id, state, reason, verdict["created_ts"])
                        con.execute("COMMIT")
                        return {"ok": False, "reason": reason}
                if candle_quality is not None and candle_quality["ok"] is not True:
                    reason = "candle_data:" + candle_quality["reason"]
                    self._update_order_status_conn(con, order_id, "rejected", reason)
                    con.execute("COMMIT")
                    return {"ok": False, "reason": reason, "candle_quality": candle_quality}
                if clock is not None or candle_quality is not None:
                    ts = datetime.fromtimestamp(_parse_created_epoch(now_ts), timezone.utc).isoformat()
            try:
                stored_meta = json.loads(order_row[6] if order_row[6] is not None else "null")
            except (TypeError, ValueError):
                con.execute("ROLLBACK")
                return {"ok": False, "reason": "invalid_stored_order_meta"}
            client_id = str(order_row[5])
            canonical_terminal = (
                client_id.startswith("paper_intent_") and client_id != "paper_intent_"
                and self._get_state_conn(con, "paper_exit_terminal:" + client_id[len("paper_intent_"):]) is not None
            )
            # A malformed marker must fail strict validation, never opt into legacy accounting.
            tagged_exit = any(isinstance(meta, dict) and (
                "paper_exit_policy" in meta or "paper_exit_id" in meta
            ) for meta in (stored_meta, order.get("meta"))) or canonical_terminal
            exit_identity = None
            if tagged_exit:
                existing = self._exit_order_conn(con, client_order_id=order_row[5])
                status = existing["status"]
                exit_identity = self._exit_identity(existing)

                def blocked(reason):
                    con.execute("COMMIT")
                    return {"ok": False, "reason": reason}

                if (exit_identity is None or self._exit_identity(order) != exit_identity
                        or existing["meta"] != order.get("meta")
                        or not self._exit_number(existing["qty"])
                        or not self._exit_number(order.get("qty"))):
                    return blocked("exit_identity_mismatch")
                if (not self._exit_number(price) or not self._exit_number(qty)
                        or not self._exit_number(fee, positive=False)):
                    return blocked("invalid_exit_fill_values")
                terminal = self._exit_terminal_conn(con, exit_identity)
                fills = self._exit_fills_conn(con, exit_identity)
                if terminal and terminal["state"] == "blocked":
                    return blocked(terminal["reason"])
                if terminal and terminal["state"] == "superseded":
                    if fills or status == "filled":
                        return blocked("exit_terminal_conflict")
                    self._supersede_exit_conn(con, exit_identity, existing)
                    return blocked("superseded")
                if status == "filled":
                    if not self._valid_exit_fill(fills, existing) or (
                        terminal and terminal.get("fill_id") != fills[0]["fill_id"]
                    ):
                        return blocked("missing_or_conflicting_fill")
                    con.execute("COMMIT")
                    return {"ok": True, "fill_id": fills[0]["fill_id"], "qty": fills[0]["qty"],
                            "fee": fills[0]["fee"], "idempotent": True}
                if terminal or fills:
                    return blocked("exit_fill_state_conflict")
                if status == "superseded":
                    self._supersede_exit_conn(con, exit_identity, existing)
                    return blocked("superseded")
                if status != "new":
                    return blocked(status)
                if existing["order_type"] == "limit" and price < existing["limit_price"]:
                    return blocked("exit_fill_below_limit")
                pos = self._get_position_conn(con, symbol)
                held = pos["qty"] if pos else 0.0
                if not self._exit_number(held, positive=False):
                    return blocked("invalid_holding")
                if held == 0:
                    self._supersede_exit_conn(con, exit_identity, existing)
                    return blocked("superseded")
                actual_qty = min(qty, order["qty"], existing["qty"], held)
                fee = float(fee) * (actual_qty / qty)
                qty = actual_qty
                con.execute("UPDATE paper_orders SET qty=? WHERE order_id=?", (qty, order_id))
            if status == "filled":
                if snapshot_quote_guard is not False:
                    receipt = self._committed_fill_receipt_conn(con, order_id, order_row[11])
                else:
                    receipt = {"ok": True, "fill_id": _paper_fill_id(order_id, price, qty),
                               "fee": float(fee), "idempotent": True}
                con.execute("COMMIT")
                return receipt
            if status in {"rejected", "canceled", "cancelled", "superseded"}:
                con.execute("COMMIT")
                return {"ok": False, "reason": status}

            quote_evidence = None
            if snapshot_quote_guard is not False:
                from services.market_data.paper_snapshot_quote import assess_paper_quote, paper_quote_fill_price

                if snapshot_quote_guard is not True:
                    con.rollback()
                    return {"ok": False, "reason": "quote_data:invalid_policy", "unresolved": True}
                quote_now = _paper_buy_now(clock)
                quote_evidence, reason = assess_paper_quote(
                    snapshot_quote, venue=order_row[8], symbol=symbol, now=quote_now,
                )
                if quote_evidence is None:
                    con.rollback()
                    return {"ok": False, "reason": "quote_data:" + reason, "unresolved": True}
                if (not self._exit_number(price) or not self._exit_number(qty)
                        or not self._exit_number(fee, positive=False)):
                    con.rollback()
                    return {"ok": False, "reason": "quote_data:invalid_fill_values", "unresolved": True}
                expected = paper_quote_fill_price(
                    quote_evidence, side=side, order_type=order_row[9], limit=order_row[10],
                    slippage_bps=snapshot_slippage_bps,
                )
                if expected is None or price != expected:
                    con.rollback()
                    return {"ok": False, "reason": "quote_data:price_model_mismatch", "unresolved": True}
                ts = datetime.fromtimestamp(_parse_created_epoch(quote_now), timezone.utc).isoformat()

            fill_id = _paper_fill_id(order_id, price, qty)
            pos = self._get_position_conn(con, symbol) or {
                "symbol": symbol,
                "qty": 0.0,
                "avg_price": 0.0,
                "realized_pnl": 0.0,
            }
            pos_qty = float(pos["qty"])
            avg = float(pos["avg_price"])
            realized_pos = float(pos["realized_pnl"])
            cash = float(self._get_state_conn(con, "cash_quote") or "0.0")
            realized_total = float(self._get_state_conn(con, "realized_pnl") or "0.0")
            fill_realized_pnl = 0.0
            if (tagged_exit or quote_evidence is not None) and not all(math.isfinite(value) for value in (
                pos_qty, avg, realized_pos, cash, realized_total,
            )):
                con.execute("ROLLBACK")
                if quote_evidence is not None:
                    return {"ok": False, "reason": "quote_data:invalid_accounting", "unresolved": True}
                return {"ok": False, "reason": "invalid_exit_accounting"}

            if side == "buy":
                cost = float(price) * float(qty) + float(fee)
                if cash + FLOAT_CASH_EPSILON < cost:
                    self._update_order_status_conn(con, order_id, "rejected", "insufficient_cash")
                    con.execute("COMMIT")
                    return {"ok": False, "reason": "insufficient_cash"}
                new_qty = pos_qty + float(qty)
                # Store fee-inclusive cost basis so later sell PnL is net of both legs.
                new_avg = ((avg * pos_qty) + (float(price) * float(qty)) + float(fee)) / new_qty if new_qty > 0 else 0.0
                new_cash = cash - cost
                if new_cash < 0.0 and abs(new_cash) <= FLOAT_CASH_EPSILON:
                    new_cash = 0.0
                new_realized_total = realized_total
                new_pos_realized = realized_pos
            else:
                if pos_qty < float(qty):
                    self._update_order_status_conn(con, order_id, "rejected", "insufficient_position")
                    con.execute("COMMIT")
                    return {"ok": False, "reason": "insufficient_position"}
                proceeds = float(price) * float(qty) - float(fee)
                fill_realized_pnl = proceeds - (avg * float(qty))
                new_qty = pos_qty - float(qty)
                new_avg = avg if new_qty > 0 else 0.0
                new_cash = cash + proceeds
                new_realized_total = realized_total + fill_realized_pnl
                new_pos_realized = realized_pos + fill_realized_pnl

            if (tagged_exit or quote_evidence is not None) and not all(math.isfinite(value) for value in (
                new_qty, new_avg, new_cash, new_realized_total, new_pos_realized, fill_realized_pnl,
            )):
                con.execute("ROLLBACK")
                if quote_evidence is not None:
                    return {"ok": False, "reason": "quote_data:invalid_accounting", "unresolved": True}
                return {"ok": False, "reason": "invalid_exit_accounting"}
            self._upsert_position_conn(
                con,
                symbol,
                new_qty,
                new_avg,
                new_pos_realized,
                updated_ts=str(ts),
            )
            self._set_state_conn(con, "cash_quote", str(float(new_cash)))
            self._set_state_conn(con, "realized_pnl", str(float(new_realized_total)))
            inserted = self._insert_fill_conn(
                con,
                {
                    "fill_id": fill_id,
                    "order_id": order_id,
                    "ts": str(ts),
                    "price": float(price),
                    "qty": float(qty),
                    "fee": float(fee),
                    "fee_currency": str(fee_currency),
                },
            )
            if inserted != 1:
                raise RuntimeError("paper_fill_insert_failed")
            if execution_identity_evidence is not None:
                # Commit fill-time evidence with accounting, never backfill on retry.
                self._set_state_conn(
                    con, "fill_execution_identity:" + fill_id,
                    json.dumps(execution_identity_evidence, sort_keys=True, allow_nan=False),
                )
            self._update_order_status_conn(con, order_id, "filled", None)
            if tagged_exit:
                self._write_exit_terminal_conn(con, exit_identity, "filled", fill_id=fill_id, qty=float(qty))
            if quote_evidence is not None:
                try:
                    con.execute(
                        "INSERT INTO paper_state(k, v) VALUES(?, ?)",
                        ("paper_fill_quote:" + fill_id, json.dumps(quote_evidence, sort_keys=True, allow_nan=False)),
                    )
                except (sqlite3.Error, TypeError, ValueError):
                    con.rollback()
                    return {"ok": False, "reason": "quote_data:evidence_unwritable", "unresolved": True}
                # Recheck after added I/O so the receipt cannot delay either
                # freshness or buy TTL past its final logical commit gate.
                final_now = _paper_buy_now(clock)
                if side == "buy":
                    final_age = _paper_buy_age_verdict(order_row[7], order_row[6], final_now, queue_origins=queue_origins)
                    if not final_age["ok"]:
                        con.rollback()
                        return {"ok": False, "reason": final_age["reason"], "unresolved": True}
                final_quote, reason = assess_paper_quote(
                    quote_evidence, venue=order_row[8], symbol=symbol, now=final_now,
                )
                if final_quote is None:
                    con.rollback()
                    return {"ok": False, "reason": "quote_data:" + reason, "unresolved": True}
            con.execute("COMMIT")
            return {
                "ok": True,
                "fill_id": fill_id,
                "fee": float(fee),
                "realized_pnl_usd": float(fill_realized_pnl),
                "pnl_usd_semantics": "net_of_fees",
                "idempotent": False,
                **({"qty": float(qty)} if tagged_exit else {}),
            }
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            con.close()

    def get_fill_quote_evidence(self, fill_id: str) -> Optional[Dict[str, Any]]:
        """Read the quote captured with this fill; never infer historical quotes."""
        raw = self.get_state("paper_fill_quote:" + str(fill_id))
        return _decode_payload(raw) if raw is not None else None

    def get_fill_execution_identity(self, fill_id: str) -> Optional[Dict[str, Any]]:
        raw = self.get_state("fill_execution_identity:" + str(fill_id))
        if raw is None:
            return None
        try:
            evidence = json.loads(raw)
            if not isinstance(evidence, dict):
                raise ValueError("invalid evidence shape")
            return evidence
        except (TypeError, ValueError):
            return {"execution_identity_fill_status": "invalid_storage"}

   
    def get_order_by_order_id(self, order_id: str) -> Optional[dict]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason, strategy_id, meta_json "
                "FROM paper_orders WHERE order_id=?",
                (str(order_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "order_id": r[0], "client_order_id": r[1], "created_ts": r[2], "ts": r[3],
                "venue": r[4], "symbol": r[5], "side": r[6], "order_type": r[7],
                "qty": r[8], "limit_price": r[9], "status": r[10], "reject_reason": r[11],
                "strategy_id": r[12], "meta": json.loads(r[13]) if r[13] else None,
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
