from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "ws_status.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS ws_status (
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  status TEXT NOT NULL,
  recv_ts_ms INTEGER NOT NULL,
  lag_ms REAL NOT NULL,
  error TEXT,
  meta_json TEXT,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (exchange, symbol)
);
CREATE TABLE IF NOT EXISTS ws_status_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  status TEXT NOT NULL,
  recv_ts_ms INTEGER NOT NULL,
  lag_ms REAL NOT NULL,
  error TEXT,
  meta_json TEXT,
  updated_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wse_recv ON ws_status_events(recv_ts_ms);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con


class WSStatusSQLite:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DB_PATH
        _connect(self.path).close()

    def upsert_status(
        self,
        *,
        exchange: str,
        symbol: str,
        status: str,
        recv_ts_ms: int,
        lag_ms: float,
        error: str | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> None:
        row = (
            str(exchange).lower().strip(),
            str(symbol).strip(),
            str(status).lower().strip(),
            int(recv_ts_ms),
            float(lag_ms),
            None if error is None else str(error),
            json.dumps(meta or {}, default=str),
            _now_iso(),
        )
        con = _connect(self.path)
        try:
            con.execute(
                "INSERT OR REPLACE INTO ws_status(exchange, symbol, status, recv_ts_ms, lag_ms, error, meta_json, updated_ts) VALUES(?,?,?,?,?,?,?,?)",
                row,
            )
            con.execute(
                "INSERT INTO ws_status_events(exchange, symbol, status, recv_ts_ms, lag_ms, error, meta_json, updated_ts) VALUES(?,?,?,?,?,?,?,?)",
                row,
            )
        finally:
            con.close()

    def get_status(self, *, exchange: str, symbol: str) -> Dict[str, Any] | None:
        con = _connect(self.path)
        try:
            r = con.execute(
                "SELECT exchange, symbol, status, recv_ts_ms, lag_ms, error, meta_json, updated_ts FROM ws_status WHERE exchange=? AND symbol=?",
                (str(exchange).lower().strip(), str(symbol).strip()),
            ).fetchone()
            if not r:
                return None
            try:
                meta = json.loads(r["meta_json"] or "{}")
            except Exception:
                meta = {}
            return {
                "exchange": r["exchange"],
                "symbol": r["symbol"],
                "status": r["status"],
                "recv_ts_ms": int(r["recv_ts_ms"]),
                "lag_ms": float(r["lag_ms"]),
                "error": r["error"],
                "meta": meta,
                "updated_ts": r["updated_ts"],
            }
        finally:
            con.close()

    def recent_events(self, *, limit: int = 200, exchange: str | None = None, symbol: str | None = None) -> List[Dict[str, Any]]:
        q = (
            "SELECT exchange, symbol, status, recv_ts_ms, lag_ms, error, meta_json, updated_ts FROM ws_status_events"
        )
        args: list[Any] = []
        where: list[str] = []
        if exchange:
            where.append("exchange=?")
            args.append(str(exchange).lower().strip())
        if symbol:
            where.append("symbol=?")
            args.append(str(symbol).strip())
        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY recv_ts_ms DESC LIMIT ?"
        args.append(int(limit))
        con = _connect(self.path)
        try:
            rows = con.execute(q, tuple(args)).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                try:
                    meta = json.loads(r["meta_json"] or "{}")
                except Exception:
                    meta = {}
                out.append(
                    {
                        "exchange": r["exchange"],
                        "symbol": r["symbol"],
                        "status": r["status"],
                        "recv_ts_ms": int(r["recv_ts_ms"]),
                        "lag_ms": float(r["lag_ms"]),
                        "error": r["error"],
                        "meta": meta,
                        "updated_ts": r["updated_ts"],
                    }
                )
            return out
        finally:
            con.close()

    def stale_symbols(self, *, max_recv_age_ms: int, now_ms: int) -> List[Dict[str, Any]]:
        con = _connect(self.path)
        try:
            rows = con.execute(
                "SELECT exchange, symbol, recv_ts_ms, status, lag_ms FROM ws_status WHERE recv_ts_ms < ? ORDER BY recv_ts_ms ASC",
                (int(now_ms) - int(max_recv_age_ms),),
            ).fetchall()
            return [
                {
                    "exchange": r["exchange"],
                    "symbol": r["symbol"],
                    "recv_ts_ms": int(r["recv_ts_ms"]),
                    "status": r["status"],
                    "lag_ms": float(r["lag_ms"]),
                    "age_ms": int(now_ms) - int(r["recv_ts_ms"]),
                }
                for r in rows
            ]
        finally:
            con.close()
