from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import os
from services.os.app_paths import data_dir, ensure_dirs
CBP_UNKNOWN_RESUBMIT_AFTER_S = float(os.environ.get("CBP_UNKNOWN_RESUBMIT_AFTER_S") or "45")
CBP_UNKNOWN_RESUBMIT_MAX = int(os.environ.get("CBP_UNKNOWN_RESUBMIT_MAX") or "1")


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
CREATE TABLE IF NOT EXISTS order_dedupe(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exchange_id TEXT NOT NULL,
  intent_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  client_order_id TEXT NOT NULL,
  remote_order_id TEXT,
  status TEXT NOT NULL,               -- created|submitted|unknown|error|terminal|acked
  created_ts_ms INTEGER NOT NULL,
  updated_ts_ms INTEGER NOT NULL,
  last_error TEXT,
  meta_json TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_od_intent ON order_dedupe(exchange_id, intent_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_od_client ON order_dedupe(exchange_id, client_order_id);
CREATE INDEX IF NOT EXISTS idx_od_status ON order_dedupe(status, updated_ts_ms);
"""

@dataclass
class OrderDedupeStore:
    exec_db: str = ""

    def __post_init__(self) -> None:
        if not self.exec_db:
            ensure_dirs()
            self.exec_db = str(data_dir() / "execution.sqlite")
        with _conn(self.exec_db) as c:
            c.executescript(DDL)
            c.commit()

    def get_by_intent(self, exchange_id: str, intent_id: str) -> Optional[Dict[str, Any]]:
        ex = (exchange_id or "").lower().strip()
        with _conn(self.exec_db) as c:
            r = c.execute(
                "SELECT * FROM order_dedupe WHERE exchange_id=? AND intent_id=? LIMIT 1",
                (ex, str(intent_id)),
            ).fetchone()
        return dict(r) if r else None

    def get_by_client(self, exchange_id: str, client_order_id: str) -> Optional[Dict[str, Any]]:
        ex = (exchange_id or "").lower().strip()
        with _conn(self.exec_db) as c:
            r = c.execute(
                "SELECT * FROM order_dedupe WHERE exchange_id=? AND client_order_id=? LIMIT 1",
                (ex, str(client_order_id)),
            ).fetchone()
        return dict(r) if r else None

    def claim(self, *, exchange_id: str, intent_id: str, symbol: str, client_order_id: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ex = (exchange_id or "").lower().strip()
        now = _now_ms()
        meta_json = json.dumps(meta or {}, default=str)[:200000]
        inserted = False
        with _conn(self.exec_db) as c:
            cur = c.execute(
                """
                INSERT OR IGNORE INTO order_dedupe(
                  exchange_id,intent_id,symbol,client_order_id,remote_order_id,status,created_ts_ms,updated_ts_ms,last_error,meta_json
                ) VALUES(?,?,?,?,NULL,'created',?,?,NULL,?)
                """,
                (ex, str(intent_id), str(symbol), str(client_order_id), now, now, meta_json),
            )
            inserted = cur.rowcount == 1
            c.commit()
        row = self.get_by_intent(ex, str(intent_id))
        if row is not None:
            row["_inserted"] = inserted
        if not row:
            raise RuntimeError("order_dedupe claim failed")
        return row

    def set_remote_id_if_empty(self, *, exchange_id: str, intent_id: str, remote_order_id: str) -> None:
        ex = (exchange_id or "").lower().strip()
        now = _now_ms()
        with _conn(self.exec_db) as c:
            c.execute(
                """
                UPDATE order_dedupe
                SET remote_order_id=COALESCE(remote_order_id, ?),
                    updated_ts_ms=?
                WHERE exchange_id=? AND intent_id=?
                """,
                (str(remote_order_id), now, ex, str(intent_id)),
            )
            c.commit()

    def mark_submitted(self, *, exchange_id: str, intent_id: str, remote_order_id: Optional[str]) -> None:
        ex = (exchange_id or "").lower().strip()
        now = _now_ms()
        with _conn(self.exec_db) as c:
            c.execute(
                """
                UPDATE order_dedupe
                SET remote_order_id=COALESCE(remote_order_id, ?),
                    status=CASE
                      WHEN status IN ('terminal','acked') THEN status
                      ELSE 'submitted'
                    END,
                    updated_ts_ms=?,
                    last_error=NULL
                WHERE exchange_id=? AND intent_id=?
                """,
                (remote_order_id, now, ex, str(intent_id)),
            )
            c.commit()

    def mark_unknown(self, *, exchange_id: str, intent_id: str, error: str) -> None:
        ex = (exchange_id or "").lower().strip()
        now = _now_ms()
        with _conn(self.exec_db) as c:
            c.execute(
                """
                UPDATE order_dedupe
                SET status=CASE
                      WHEN status IN ('terminal','acked') THEN status
                      ELSE 'unknown'
                    END,
                    updated_ts_ms=?,
                    last_error=?
                WHERE exchange_id=? AND intent_id=?
                """,
                (now, str(error)[:5000], ex, str(intent_id)),
            )
            c.commit()

    def mark_error(self, *, exchange_id: str, intent_id: str, error: str) -> None:
        ex = (exchange_id or "").lower().strip()
        now = _now_ms()
        with _conn(self.exec_db) as c:
            c.execute(
                """
                UPDATE order_dedupe
                SET status=CASE
                      WHEN status IN ('terminal','acked') THEN status
                      ELSE 'error'
                    END,
                    updated_ts_ms=?,
                    last_error=?
                WHERE exchange_id=? AND intent_id=?
                """,
                (now, str(error)[:5000], ex, str(intent_id)),
            )
            c.commit()

    def mark_terminal(self, *, exchange_id: str, intent_id: str, terminal_status: str) -> None:
        ex = (exchange_id or "").lower().strip()
        now = _now_ms()
        with _conn(self.exec_db) as c:
            c.execute(
                """
                UPDATE order_dedupe
                SET status='terminal',
                    updated_ts_ms=?,
                    last_error=NULL
                WHERE exchange_id=? AND intent_id=?
                """,
                (now, ex, str(intent_id)),
            )
            c.commit()

    def list_needs_reconcile(self, *, exchange_id: str, limit: int = 200) -> list[Dict[str, Any]]:
        ex = (exchange_id or "").lower().strip()
        with _conn(self.exec_db) as c:
            rows = c.execute(
                """
                SELECT * FROM order_dedupe
                WHERE exchange_id=? AND status IN ('created','submitted','unknown','error')
                ORDER BY updated_ts_ms DESC
                LIMIT ?
                """,
                (ex, int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]
