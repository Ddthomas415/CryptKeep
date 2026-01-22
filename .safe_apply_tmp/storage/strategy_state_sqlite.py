from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "strategy_state.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS strategy_state (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);
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

class StrategyStateSQLite:
    def __init__(self) -> None:
        _connect().close()

    def get(self, k: str) -> Optional[str]:
        con = _connect()
        try:
            r = con.execute("SELECT v FROM strategy_state WHERE k=?", (str(k),)).fetchone()
            return r[0] if r else None
        finally:
            con.close()

    def set(self, k: str, v: str) -> None:
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO strategy_state(k,v,updated_ts) VALUES(?,?,?)", (str(k), str(v), _now()))
        finally:
            con.close()
