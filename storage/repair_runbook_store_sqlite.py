from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteRepairRunbookStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _ensure(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS repair_plans(
                  plan_id TEXT PRIMARY KEY,
                  exchange TEXT NOT NULL,
                  plan_hash TEXT NOT NULL,
                  summary_json TEXT NOT NULL,
                  actions_json TEXT NOT NULL,
                  meta_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_ts TEXT NOT NULL,
                  approved_ts TEXT,
                  executed_ts TEXT
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS repair_events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plan_id TEXT NOT NULL,
                  ts TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  message TEXT NOT NULL,
                  payload_json TEXT NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_repair_events_plan_ts ON repair_events(plan_id, id DESC)")
        finally:
            con.close()

    def create_plan_sync(
        self,
        *,
        plan_id: str,
        exchange: str,
        plan_hash: str,
        summary: Any,
        actions: Any,
        meta: Any = None,
    ) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO repair_plans(plan_id, exchange, plan_hash, summary_json, actions_json, meta_json, status, created_ts, approved_ts, executed_ts) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    str(plan_id),
                    str(exchange),
                    str(plan_hash),
                    json.dumps(summary or {}, sort_keys=True),
                    json.dumps(actions or [], sort_keys=True),
                    json.dumps(meta or {}, sort_keys=True),
                    "draft",
                    _now(),
                    None,
                    None,
                ),
            )
            con.execute(
                "INSERT INTO repair_events(plan_id, ts, event_type, message, payload_json) VALUES(?,?,?,?,?)",
                (str(plan_id), _now(), "plan_created", "repair plan created", json.dumps({"exchange": exchange}, sort_keys=True)),
            )
        finally:
            con.close()

    def add_event_sync(self, plan_id: str, event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO repair_events(plan_id, ts, event_type, message, payload_json) VALUES(?,?,?,?,?)",
                (str(plan_id), _now(), str(event_type), str(message), json.dumps(payload or {}, sort_keys=True)),
            )
        finally:
            con.close()

    def get_plan_sync(self, plan_id: str) -> dict[str, Any] | None:
        con = self._connect()
        try:
            row = con.execute(
                "SELECT plan_id, exchange, plan_hash, summary_json, actions_json, meta_json, status, created_ts, approved_ts, executed_ts FROM repair_plans WHERE plan_id=?",
                (str(plan_id),),
            ).fetchone()
        finally:
            con.close()
        if not row:
            return None
        return {
            "plan_id": str(row[0]),
            "exchange": str(row[1]),
            "plan_hash": str(row[2]),
            "summary": json.loads(row[3] or "{}"),
            "actions": json.loads(row[4] or "[]"),
            "meta": json.loads(row[5] or "{}"),
            "status": str(row[6]),
            "created_ts": row[7],
            "approved_ts": row[8],
            "executed_ts": row[9],
        }

    def list_events_sync(self, plan_id: str, limit: int = 500) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT ts, event_type, message, payload_json FROM repair_events WHERE plan_id=? ORDER BY id DESC LIMIT ?",
                (str(plan_id), int(limit)),
            ).fetchall()
        finally:
            con.close()
        out: list[dict[str, Any]] = []
        for r in rows:
            try:
                payload = json.loads(r[3] or "{}")
            except Exception:
                payload = {}
            out.append({"ts": str(r[0]), "event_type": str(r[1]), "message": str(r[2]), "payload": payload})
        out.reverse()
        return out
