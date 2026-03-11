from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _iso_from_ts_ms(ts_ms: int) -> str:
    return datetime.fromtimestamp(float(ts_ms) / 1000.0, tz=timezone.utc).isoformat()


class OpsEventStore:
    def __init__(self, exec_db: str):
        self.exec_db = str(exec_db)
        Path(self.exec_db).parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _conn(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.exec_db)
        con.row_factory = sqlite3.Row
        return con

    def _ensure(self) -> None:
        with self._conn() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS ops_events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  message TEXT NOT NULL,
                  meta_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_ops_events_ts ON ops_events(ts)")

    def add(
        self,
        *,
        severity: str,
        event_type: str,
        message: str,
        meta: dict[str, Any] | None = None,
        ts_ms: int | None = None,
    ) -> None:
        ts = _iso_from_ts_ms(int(ts_ms)) if ts_ms is not None else _now()
        with self._conn() as con:
            con.execute(
                "INSERT INTO ops_events(ts, severity, event_type, message, meta_json) VALUES(?,?,?,?,?)",
                (ts, str(severity), str(event_type), str(message), json.dumps(meta or {}, sort_keys=True)),
            )


    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT id, ts, severity, event_type, message, meta_json FROM ops_events ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            try:
                meta = json.loads(row["meta_json"] or "{}")
            except Exception:
                meta = {}
            out.append(
                {
                    "id": int(row["id"]),
                    "ts": str(row["ts"]),
                    "severity": str(row["severity"]),
                    "event_type": str(row["event_type"]),
                    "message": str(row["message"]),
                    "meta": meta,
                }
            )
        return out
