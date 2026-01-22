from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import datetime
import sqlite3
from pathlib import Path

def _utc_day_key(now: Optional[datetime.datetime] = None) -> str:
    n = now or datetime.datetime.utcnow()
    return n.strftime("%Y-%m-%d")

def _utc_iso(now: Optional[datetime.datetime] = None) -> str:
    n = now or datetime.datetime.utcnow()
    return n.isoformat() + "Z"

class RiskDailyDB:
    """
    Deterministic daily rollup for LIVE gates.
    Stored in exec_db table: risk_daily(day, trades, realized_pnl_usd, fees_usd, updated_at)
    """
    def __init__(self, exec_db: str):
        self.exec_db = exec_db
        Path(exec_db).parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.exec_db)
        c.row_factory = sqlite3.Row
        return c

    def _ensure(self) -> None:
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS risk_daily(
              day TEXT PRIMARY KEY,
              trades INTEGER NOT NULL DEFAULT 0,
              realized_pnl_usd REAL NOT NULL DEFAULT 0,
              fees_usd REAL NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL
            );
            """)

    def get(self, day: Optional[str] = None) -> Dict[str, Any]:
        d = day or _utc_day_key()
        with self._conn() as c:
            r = c.execute("SELECT day,trades,realized_pnl_usd,fees_usd,updated_at FROM risk_daily WHERE day=?", (d,)).fetchone()
            if r:
                return dict(r)
            c.execute(
                "INSERT INTO risk_daily(day,trades,realized_pnl_usd,fees_usd,updated_at) VALUES(?,?,?,?,?)",
                (d, 0, 0.0, 0.0, _utc_iso())
            )
            return {"day": d, "trades": 0, "realized_pnl_usd": 0.0, "fees_usd": 0.0, "updated_at": _utc_iso()}

    def incr_trades(self, n: int = 1, day: Optional[str] = None) -> int:
        d = day or _utc_day_key()
        with self._conn() as c:
            row = self.get(d)
            new_val = int(row["trades"]) + int(n)
            c.execute("UPDATE risk_daily SET trades=?, updated_at=? WHERE day=?", (new_val, _utc_iso(), d))
            return new_val

    def add_pnl(self, realized_pnl_usd: float = 0.0, fee_usd: float = 0.0, day: Optional[str] = None) -> Dict[str, Any]:
        d = day or _utc_day_key()
        with self._conn() as c:
            row = self.get(d)
            rp = float(row["realized_pnl_usd"]) + float(realized_pnl_usd)
            fu = float(row["fees_usd"]) + float(fee_usd)
            c.execute("UPDATE risk_daily SET realized_pnl_usd=?, fees_usd=?, updated_at=? WHERE day=?", (rp, fu, _utc_iso(), d))
            return self.get(d)

    def realized_today_usd(self) -> float:
        return float(self.get(_utc_day_key()).get("realized_pnl_usd", 0.0))

    def trades_today(self) -> int:
        return int(self.get(_utc_day_key()).get("trades", 0))
