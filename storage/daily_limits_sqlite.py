from __future__ import annotations

import sqlite3

# OWNERSHIP: DailyLimitsSQLite writes to data/daily_limits.sqlite (a separate file).
# This is NOT the same store used by LiveGateDB in services/risk/live_risk_gates_phase82.py,
# which writes daily_limits to execution.sqlite.
# Use DailyLimitsSQLite for: standalone paper-mode daily tracking.
# Use LiveGateDB for: live-mode gate enforcement in submit_pending_live().
# Do not add new daily limit logic here without updating the ownership comment.
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from services.os.app_paths import data_dir

DB_PATH = data_dir() / "daily_limits.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS daily_limits (
  day TEXT PRIMARY KEY,
  trades INTEGER NOT NULL DEFAULT 0,
  realized_pnl_usd REAL NOT NULL DEFAULT 0.0,
  updated_at TEXT NOT NULL
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_day_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class DailyLimitsSQLite:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect():
            pass

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db_path, timeout=30, isolation_level=None, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        for stmt in SCHEMA.strip().split(";"):
            s = stmt.strip()
            if s:
                con.execute(s)
        return con

    def day_row(self, day: str | None = None) -> Dict[str, Any]:
        d = str(day or _utc_day_key())
        now = _now_iso()
        with self._connect() as con:
            row = con.execute(
                "SELECT day, trades, realized_pnl_usd, updated_at FROM daily_limits WHERE day=?",
                (d,),
            ).fetchone()
            if row:
                return {
                    "day": row["day"],
                    "trades": int(row["trades"]),
                    "realized_pnl_usd": float(row["realized_pnl_usd"]),
                    "updated_at": row["updated_at"],
                }
            con.execute(
                "INSERT INTO daily_limits(day, trades, realized_pnl_usd, updated_at) VALUES(?,?,?,?)",
                (d, 0, 0.0, now),
            )
            return {"day": d, "trades": 0, "realized_pnl_usd": 0.0, "updated_at": now}

    def incr_trades(self, n: int = 1, *, day: str | None = None) -> int:
        row = self.day_row(day=day)
        d = row["day"]
        val = int(row["trades"]) + int(n)
        now = _now_iso()
        with self._connect() as con:
            con.execute("UPDATE daily_limits SET trades=?, updated_at=? WHERE day=?", (val, now, d))
        return val

    def set_realized_pnl_usd(self, value: float, *, day: str | None = None) -> float:
        row = self.day_row(day=day)
        d = row["day"]
        now = _now_iso()
        v = float(value)
        with self._connect() as con:
            con.execute("UPDATE daily_limits SET realized_pnl_usd=?, updated_at=? WHERE day=?", (v, now, d))
        return v

    def add_realized_pnl_usd(self, delta: float, *, day: str | None = None) -> float:
        row = self.day_row(day=day)
        next_v = float(row["realized_pnl_usd"]) + float(delta)
        self.set_realized_pnl_usd(next_v, day=row["day"])
        return next_v
