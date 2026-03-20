from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "idempotency.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS idempotency (
  k TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  result_json TEXT,
  error TEXT,
  updated_ts TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idem_status ON idempotency(status);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con


class IdempotencySQLite:
    def __init__(self) -> None:
        _connect().close()

    def get(self, key: str) -> Optional[dict]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT k, status, result_json, error, updated_ts FROM idempotency WHERE k=?",
                (str(key),),
            ).fetchone()
            if not r:
                return None
            result = None
            if r[2]:
                try:
                    result = json.loads(r[2])
                except Exception:
                    result = None
            return {"key": r[0], "status": r[1], "result": result, "error": r[3], "updated_ts": r[4]}
        finally:
            con.close()

    def put_success(self, key: str, result: Any) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO idempotency(k, status, result_json, error, updated_ts) VALUES(?,?,?,?,?)",
                (str(key), "success", json.dumps(result, ensure_ascii=False), None, _now()),
            )
        finally:
            con.close()

    def put_error(self, key: str, error: str) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO idempotency(k, status, result_json, error, updated_ts) VALUES(?,?,?,?,?)",
                (str(key), "error", None, str(error), _now()),
            )
        finally:
            con.close()




# Human Review Required: compatibility wrapper; verify method/constructor semantics.
class OrderDedupeStore(IdempotencySQLite):
    def __init__(self, exec_db=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exec_db = exec_db
