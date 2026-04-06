from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

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
"""

_ALLOWED_STATUS_TRANSITIONS = {
    "pending": {"submitted", "canceled", "error"},
    "submitted": {"filled", "canceled", "error", "partially_filled"},
    "partially_filled": {"filled", "canceled", "error"},
    "filled": set(),
    "canceled": set(),
    "error": set(),
}


def _normalize_status(status: Any) -> str:
    return str(status or "").strip().lower()


def _transition_allowed(current: str, nxt: str) -> bool:
    if current == nxt:
        return True
    return nxt in _ALLOWED_STATUS_TRANSITIONS.get(current, set())


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

    def set_intent_status(self, *, intent_id: str, status: str, reason: Optional[str] = None) -> None:
        with _conn(self.path) as c:
            row = c.execute(
                "SELECT status FROM intents WHERE intent_id=?",
                (str(intent_id),),
            ).fetchone()
            if row is None:
                return
            current = _normalize_status(row["status"])
            nxt = _normalize_status(status)
            if not _transition_allowed(current, nxt):
                return
            c.execute(
                "UPDATE intents SET status=?, reason=? WHERE intent_id=?",
                (str(nxt), reason, str(intent_id)),
            )
            c.commit()

    def add_fill(self, *, intent_id: str, ts_ms: int, price: float, qty: float, fee: float, fee_ccy: str, meta: Optional[Dict[str, Any]] = None) -> None:
        trade_id = _trade_id_from_meta(meta)
        with _conn(self.path) as c:
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
