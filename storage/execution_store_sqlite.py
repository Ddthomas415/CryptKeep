from __future__ import annotations

import json
import math
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from services.execution.intent_lifecycle import (
    EXECUTION_STORE_STATUS_TRANSITIONS,
    normalize_execution_store_status,
)
from services.os.app_paths import data_dir, ensure_dirs

def _now_ms() -> int:
    return int(time.time() * 1000)

def _conn(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    c = sqlite3.connect(path, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c

DDL = """
CREATE TABLE IF NOT EXISTS intents(
  intent_id TEXT PRIMARY KEY,
  ts_ms INTEGER NOT NULL,
  mode TEXT NOT NULL,                 -- paper|live
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,                 -- buy|sell
  order_type TEXT NOT NULL,           -- market|limit
  qty REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL,               -- pending|submitted|filled|canceled|error
  reason TEXT,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_intents_lookup
  ON intents(mode, exchange, symbol, status, ts_ms);

CREATE TABLE IF NOT EXISTS fills(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  intent_id TEXT NOT NULL,
  ts_ms INTEGER NOT NULL,
  price REAL NOT NULL,
  qty REAL NOT NULL,
  fee REAL NOT NULL,
  fee_ccy TEXT NOT NULL,
  meta_json TEXT,
  trade_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_fills_intent_ts ON fills(intent_id, ts_ms);

CREATE TABLE IF NOT EXISTS symbol_locks(
  symbol TEXT PRIMARY KEY,
  locked_until_ms INTEGER NOT NULL,
  loss_count INTEGER NOT NULL DEFAULT 0,
  reason TEXT,
  created_ts_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS symbol_loss_fill_events(
  venue TEXT NOT NULL,
  fill_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  realized_pnl_usd REAL NOT NULL,
  loss_count INTEGER NOT NULL,
  PRIMARY KEY(venue, fill_id)
);

CREATE TABLE IF NOT EXISTS symbol_loss_cutover(
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  activated_at_ms INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS symbol_loss_legacy_fills(
  venue TEXT NOT NULL,
  fill_id TEXT NOT NULL,
  PRIMARY KEY(venue, fill_id)
);
CREATE TABLE IF NOT EXISTS reconcile_fill_deliveries(
  intent_id TEXT NOT NULL,
  venue TEXT NOT NULL,
  fill_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)),
  PRIMARY KEY(venue, fill_id),
  UNIQUE(intent_id, fill_id)
);
"""

def _trade_id_from_meta(meta: Optional[Dict[str, Any]]) -> str | None:
    if not isinstance(meta, dict):
        return None
    for key in ("trade_id", "tradeId", "fill_id", "fillId", "id"):
        value = meta.get(key)
        if value:
            trade_id = str(value).strip()
            if trade_id:
                return trade_id
    raw_trade = meta.get("raw_trade")
    if isinstance(raw_trade, dict):
        for key in ("trade_id", "tradeId", "fill_id", "fillId", "id"):
            value = raw_trade.get(key)
            if value:
                trade_id = str(value).strip()
                if trade_id:
                    return trade_id
    return None

@dataclass
class ExecutionStore:
    path: str = ""

    def __post_init__(self) -> None:
        if not self.path:
            ensure_dirs()
            self.path = str(data_dir() / "execution.sqlite")
        with _conn(self.path) as c:
            c.executescript(DDL)
            cols = {str(row["name"]) for row in c.execute("PRAGMA table_info(fills)").fetchall()}
            if "trade_id" not in cols:
                c.execute("ALTER TABLE fills ADD COLUMN trade_id TEXT")
            c.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_fills_intent_trade_id
                ON fills(intent_id, trade_id)
                WHERE trade_id IS NOT NULL
                """
            )
            tables = {str(r[0]) for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if "symbol_locks" not in tables:
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS symbol_locks(
                        symbol TEXT PRIMARY KEY,
                        locked_until_ms INTEGER NOT NULL,
                        loss_count INTEGER NOT NULL DEFAULT 0,
                        reason TEXT,
                        created_ts_ms INTEGER NOT NULL
                    )
                    """
                )
            c.commit()

    def list_intents(self, *, mode: str, exchange: str, symbol: str, status: str, limit: int = 200) -> List[Dict[str, Any]]:
        with _conn(self.path) as c:
            rows = c.execute(
                """
                SELECT intent_id, ts_ms, mode, exchange, symbol, side, order_type, qty, limit_price, status, reason, meta_json
                FROM intents
                WHERE mode=? AND exchange=? AND symbol=? AND status=?
                ORDER BY ts_ms DESC
                LIMIT ?
                """,
                (str(mode), str(exchange), str(symbol), str(status), int(limit)),
            ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["meta"] = json.loads(d.get("meta_json") or "{}")
            except Exception:
                d["meta"] = {}
            out.append(d)
        return out

    def set_intent_status(self, *, intent_id: str, status: str, reason: Optional[str] = None) -> bool:
        """Transition an intent status atomically.

        The legal predecessor set is derived from the shared lifecycle map and
        enforced inside the UPDATE, so racing writers cannot both pass a stale
        Python-side check and overwrite each other's terminal status.
        """
        nxt = normalize_execution_store_status(status)
        allowed_from = {
            cur
            for cur, successors in EXECUTION_STORE_STATUS_TRANSITIONS.items()
            if nxt in successors
        }
        allowed_from.add(nxt)  # same-status writes are idempotent.
        placeholders = ",".join("?" for _ in allowed_from)

        with _conn(self.path) as c:
            cur = c.execute(
                f"""
                UPDATE intents
                   SET status=?, reason=?
                 WHERE intent_id=?
                   AND LOWER(TRIM(status)) IN ({placeholders})
                """,
                (str(nxt), reason, str(intent_id), *sorted(allowed_from)),
            )
            c.commit()
            return cur.rowcount > 0

    def add_fill(self, *, intent_id: str, ts_ms: int, price: float, qty: float, fee: float, fee_ccy: str, meta: Optional[Dict[str, Any]] = None, canonical_fill: Optional[Dict[str, Any]] = None, max_recorded_qty: float | None = None) -> None:
        trade_id = _trade_id_from_meta(meta)
        payload = None
        if canonical_fill is not None:
            if not trade_id or str(canonical_fill.get("fill_id") or "") != trade_id or not canonical_fill.get("venue"):
                raise ValueError("invalid reconcile fill identity")
            payload = json.dumps(canonical_fill, sort_keys=True, allow_nan=False)
        with _conn(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            if max_recorded_qty is not None:
                maximum = float(max_recorded_qty)
                if not math.isfinite(maximum) or maximum < 0:
                    raise ValueError("invalid reported filled quantity")
                rows = c.execute(
                    "SELECT qty, trade_id FROM fills WHERE intent_id=?", (intent_id,),
                ).fetchall()
                total = 0.0
                duplicate = False
                for row in rows:
                    recorded = float(row["qty"])
                    if not math.isfinite(recorded) or recorded <= 0:
                        raise ValueError("invalid recorded fill quantity")
                    total += recorded
                    duplicate = duplicate or (trade_id is not None and row["trade_id"] == trade_id)
                proposed = float(qty)
                if not math.isfinite(proposed) or proposed <= 0:
                    raise ValueError("invalid proposed fill quantity")
                after = total if duplicate else total + proposed
                if after > maximum and not math.isclose(after, maximum, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError("recorded fills exceed reported filled quantity")
            if payload is not None:
                existing = c.execute(
                    "SELECT intent_id, payload_json FROM reconcile_fill_deliveries WHERE venue=? AND fill_id=?",
                    (str(canonical_fill["venue"]), trade_id),
                ).fetchone()
                if existing and (existing["intent_id"] != intent_id or existing["payload_json"] != payload):
                    raise ValueError("conflicting reconcile fill delivery")
                c.execute(
                    "INSERT OR IGNORE INTO reconcile_fill_deliveries(intent_id,venue,fill_id,payload_json) VALUES(?,?,?,?)",
                    (intent_id, str(canonical_fill["venue"]), trade_id, payload),
                )
            c.execute(
                """
                INSERT OR IGNORE INTO fills(intent_id, ts_ms, price, qty, fee, fee_ccy, meta_json, trade_id)
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    str(intent_id),
                    int(ts_ms),
                    float(price),
                    float(qty),
                    float(fee),
                    str(fee_ccy),
                    json.dumps(meta or {}, default=str)[:200000],
                    trade_id,
                ),
            )
            c.commit()

    def pending_reconcile_fills(self, *, intent_id: str) -> List[Dict[str, Any]]:
        with _conn(self.path) as c:
            rows = c.execute(
                "SELECT payload_json FROM reconcile_fill_deliveries WHERE intent_id=? AND completed=0 ORDER BY rowid",
                (intent_id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def complete_reconcile_fill(self, *, venue: str, fill_id: str) -> None:
        with _conn(self.path) as c:
            result = c.execute(
                "UPDATE reconcile_fill_deliveries SET completed=1 WHERE venue=? AND fill_id=?",
                (venue, fill_id),
            )
            if result.rowcount != 1:
                raise RuntimeError("missing reconcile fill delivery")
            c.commit()

    def reconcile_fill_coverage(self, *, intent_id: str) -> Dict[str, Any]:
        with _conn(self.path) as c:
            rows = c.execute(
                "SELECT f.qty, d.completed FROM fills f LEFT JOIN reconcile_fill_deliveries d "
                "ON d.intent_id=f.intent_id AND d.fill_id=f.trade_id WHERE f.intent_id=?",
                (intent_id,),
            ).fetchall()
        quantity = 0.0
        complete = True
        for row in rows:
            qty = float(row["qty"])
            if not math.isfinite(qty) or qty <= 0:
                raise ValueError("invalid recorded fill quantity")
            quantity += qty
            complete = complete and row["completed"] == 1
        return {"qty": quantity, "complete": complete}

    def list_fill_trade_ids(self, *, intent_id: str, limit: int = 2000) -> List[str]:
        with _conn(self.path) as c:
            rows = c.execute(
                """
                SELECT trade_id, meta_json
                FROM fills
                WHERE intent_id=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (str(intent_id), int(limit)),
            ).fetchall()

        out: List[str] = []
        for r in rows:
            tid = str(r["trade_id"] or "").strip()
            if not tid:
                try:
                    meta = json.loads(r["meta_json"] or "{}")
                except Exception:
                    meta = {}
                tid = str((meta or {}).get("trade_id") or "").strip()
            if tid:
                out.append(tid)
        return out

    # Optional helper (not required by live_executor, but useful)

    def get_symbol_lock(self, symbol: str) -> Dict[str, Any] | None:
        with _conn(self.path) as c:
            row = c.execute(
                """
                SELECT symbol, locked_until_ms, loss_count, reason, created_ts_ms
                FROM symbol_locks
                WHERE symbol=?
                """,
                (str(symbol),),
            ).fetchone()
        if row is None:
            return None
        if int(row["locked_until_ms"]) <= _now_ms():
            return None
        return dict(row)

    def set_symbol_lock(self, symbol: str, locked_until_ms: int, loss_count: int, reason: str) -> None:
        with _conn(self.path) as c:
            c.execute(
                """
                INSERT INTO symbol_locks(symbol, locked_until_ms, loss_count, reason, created_ts_ms)
                VALUES(?,?,?,?,?)
                ON CONFLICT(symbol) DO UPDATE SET
                    locked_until_ms=excluded.locked_until_ms,
                    loss_count=excluded.loss_count,
                    reason=excluded.reason,
                    created_ts_ms=excluded.created_ts_ms
                """,
                (str(symbol), int(locked_until_ms), int(loss_count), str(reason), _now_ms()),
            )
            c.commit()

    def increment_symbol_loss(self, symbol: str, *, loss_limit: int, lock_duration_ms: int) -> int:
        with _conn(self.path) as c:
            row = c.execute(
                "SELECT loss_count FROM symbol_locks WHERE symbol=?",
                (str(symbol),),
            ).fetchone()
            current = int(row["loss_count"]) if row else 0
            new_count = current + 1
            if new_count >= loss_limit:
                locked_until = _now_ms() + int(lock_duration_ms)
                c.execute(
                    """
                    INSERT INTO symbol_locks(symbol, locked_until_ms, loss_count, reason, created_ts_ms)
                    VALUES(?,?,?,?,?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        locked_until_ms=excluded.locked_until_ms,
                        loss_count=excluded.loss_count,
                        reason=excluded.reason,
                        created_ts_ms=excluded.created_ts_ms
                    """,
                    (str(symbol), locked_until, new_count, f"consecutive_losses={new_count}", _now_ms()),
                )
            else:
                c.execute(
                    """
                    INSERT INTO symbol_locks(symbol, locked_until_ms, loss_count, reason, created_ts_ms)
                    VALUES(?,0,?,?,?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        loss_count=excluded.loss_count,
                        reason=excluded.reason
                    """,
                    (str(symbol), new_count, f"loss_count={new_count}", _now_ms()),
                )
            c.commit()
        return new_count

    def activate_symbol_loss_cutover(self) -> int:
        with _conn(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            existing = c.execute(
                "SELECT activated_at_ms FROM symbol_loss_cutover WHERE singleton=1"
            ).fetchone()
            if existing is not None:
                return int(existing[0])
            journal_exists = c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='canonical_fills'"
            ).fetchone()
            if journal_exists:
                # Snapshot identity, not exchange time: late arrivals remain new evidence.
                c.execute(
                    "INSERT INTO symbol_loss_legacy_fills(venue, fill_id) "
                    "SELECT f.venue, f.fill_id FROM canonical_fills f WHERE NOT EXISTS "
                    "(SELECT 1 FROM symbol_loss_fill_events e "
                    "WHERE e.venue=f.venue AND e.fill_id=f.fill_id)"
                )
            activated_at = _now_ms()
            c.execute("INSERT INTO symbol_loss_cutover VALUES(1,?)", (activated_at,))
            c.commit()
        return activated_at

    def apply_symbol_loss_fill_once(
        self, *, venue: str, fill_id: str, symbol: str,
        realized_pnl_usd: float, loss_limit: int, lock_duration_ms: int,
        require_journal_order: bool = False,
    ) -> int:
        pnl = float(realized_pnl_usd)
        if not venue or not fill_id or not symbol or not math.isfinite(pnl):
            raise ValueError("invalid symbol loss fill")
        if loss_limit < 1 or lock_duration_ms < 0:
            raise ValueError("invalid symbol loss policy")
        with _conn(self.path) as c:
            # Serialize deduplication and the counter update, including competing sinks.
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM symbol_loss_cutover WHERE singleton=1").fetchone() is None:
                raise RuntimeError("symbol loss cutover not activated")
            legacy = c.execute(
                "SELECT 1 FROM symbol_loss_legacy_fills WHERE venue=? AND fill_id=?",
                (venue, fill_id),
            ).fetchone()
            if legacy:
                current = c.execute(
                    "SELECT loss_count FROM symbol_locks WHERE symbol=?", (symbol,),
                ).fetchone()
                return int(current[0]) if current else 0
            prior = c.execute(
                "SELECT symbol, realized_pnl_usd, loss_count FROM symbol_loss_fill_events "
                "WHERE venue=? AND fill_id=?", (venue, fill_id),
            ).fetchone()
            if prior is not None:
                if prior["symbol"] != symbol or float(prior["realized_pnl_usd"]) != pnl:
                    raise ValueError("conflicting symbol loss fill replay")
                return int(prior["loss_count"])
            if require_journal_order:
                recorded = c.execute(
                    "SELECT rowid, symbol FROM canonical_fills WHERE venue=? AND fill_id=?",
                    (venue, fill_id),
                ).fetchone()
                if recorded is None or recorded["symbol"] != symbol:
                    raise ValueError("missing or conflicting journal loss identity")
                # Counter scope is per symbol across venues: use the same scope here.
                earlier = c.execute(
                    "SELECT 1 FROM canonical_fills f WHERE f.symbol=? AND f.rowid<? "
                    "AND NOT EXISTS (SELECT 1 FROM symbol_loss_legacy_fills l "
                    "WHERE l.venue=f.venue AND l.fill_id=f.fill_id) "
                    "AND NOT EXISTS (SELECT 1 FROM symbol_loss_fill_events e "
                    "WHERE e.venue=f.venue AND e.fill_id=f.fill_id) LIMIT 1",
                    (symbol, recorded["rowid"]),
                ).fetchone()
                if earlier:
                    raise RuntimeError("earlier journal loss event remains unapplied")
            row = c.execute(
                "SELECT loss_count, locked_until_ms FROM symbol_locks WHERE symbol=?",
                (symbol,),
            ).fetchone()
            count = (int(row["loss_count"]) if row else 0) + 1 if pnl < 0 else 0
            now = _now_ms()
            locked_until = (
                now + int(lock_duration_ms) if count >= loss_limit
                else int(row["locked_until_ms"]) if pnl < 0 and row else 0
            )
            reason = (
                f"consecutive_losses={count}" if count >= loss_limit
                else f"loss_count={count}" if pnl < 0 else "reset_on_profit"
            )
            c.execute(
                "INSERT INTO symbol_locks VALUES(?,?,?,?,?) ON CONFLICT(symbol) DO UPDATE SET "
                "locked_until_ms=excluded.locked_until_ms, loss_count=excluded.loss_count, "
                "reason=excluded.reason, created_ts_ms=excluded.created_ts_ms",
                (symbol, locked_until, count, reason, now),
            )
            c.execute(
                "INSERT INTO symbol_loss_fill_events VALUES(?,?,?,?,?)",
                (venue, fill_id, symbol, pnl, count),
            )
            c.commit()
        return count

    def upsert_intent(self, row: Dict[str, Any]) -> None:
        with _conn(self.path) as c:
            c.execute(
                """
                INSERT INTO intents(intent_id, ts_ms, mode, exchange, symbol, side, order_type, qty, limit_price, status, reason, meta_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(intent_id) DO UPDATE SET
                  ts_ms=excluded.ts_ms,
                  mode=excluded.mode,
                  exchange=excluded.exchange,
                  symbol=excluded.symbol,
                  side=excluded.side,
                  order_type=excluded.order_type,
                  qty=excluded.qty,
                  limit_price=excluded.limit_price,
                  status=excluded.status,
                  reason=excluded.reason,
                  meta_json=excluded.meta_json
                """,
                (
                    str(row["intent_id"]),
                    int(row.get("ts_ms") or _now_ms()),
                    str(row.get("mode") or "paper"),
                    str(row.get("exchange") or ""),
                    str(row.get("symbol") or ""),
                    str(row.get("side") or ""),
                    str(row.get("order_type") or "market"),
                    float(row.get("qty") or 0.0),
                    (None if row.get("limit_price") is None else float(row["limit_price"])),
                    str(row.get("status") or "pending"),
                    (None if row.get("reason") is None else str(row["reason"])),
                    json.dumps(row.get("meta") or {}, default=str)[:200000],
                ),
            )
            c.commit()
