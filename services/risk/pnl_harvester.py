from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from services.admin.config_editor import load_user_yaml
from services.os.app_paths import data_dir
from storage.daily_limits_sqlite import DailyLimitsSQLite


def _utc_day_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _cfg() -> Dict[str, Any]:
    cfg = load_user_yaml()
    ex = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    return {
        "exec_db_path": str(ex.get("db_path") or (data_dir() / "execution.sqlite")),
        "pnl_table": str((risk.get("pnl_harvester") or {}).get("table") or "trade_journal"),
    }


def _sum_realized_pnl_for_day(*, db_path: Path, day: str, preferred_table: str = "trade_journal") -> float:
    if not db_path.exists():
        return 0.0
    con = sqlite3.connect(db_path)
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        candidates = [preferred_table, "trade_journal", "fills", "paper_fills"]
        for table in candidates:
            if table not in tables:
                continue
            cols = {r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}
            if "realized_pnl_usd" not in cols:
                continue
            day_col = None
            for c in ("closed_ts", "ts", "timestamp", "created_ts", "updated_ts"):
                if c in cols:
                    day_col = c
                    break
            try:
                if day_col:
                    r = con.execute(
                        f"SELECT COALESCE(SUM(realized_pnl_usd),0.0) FROM {table} WHERE substr({day_col},1,10)=?",
                        (str(day),),
                    ).fetchone()
                else:
                    r = con.execute(f"SELECT COALESCE(SUM(realized_pnl_usd),0.0) FROM {table}").fetchone()
                return float(r[0] if r and r[0] is not None else 0.0)
            except Exception:
                continue
        return 0.0
    finally:
        con.close()


class PnlHarvester:
    def __init__(self, *, exec_db_path: str | Path | None = None, daily_db_path: str | Path | None = None) -> None:
        cfg = _cfg()
        self.exec_db_path = Path(exec_db_path or cfg["exec_db_path"])
        self.table_name = str(cfg["pnl_table"])
        self.daily = DailyLimitsSQLite(db_path=daily_db_path)

    def realized_pnl_usd(self, *, day: str | None = None) -> float:
        d = str(day or _utc_day_key())
        return _sum_realized_pnl_for_day(db_path=self.exec_db_path, day=d, preferred_table=self.table_name)

    def harvest(self, *, day: str | None = None) -> Dict[str, Any]:
        d = str(day or _utc_day_key())
        pnl = self.realized_pnl_usd(day=d)
        self.daily.set_realized_pnl_usd(float(pnl), day=d)
        row = self.daily.day_row(day=d)
        return {"ok": True, "day": d, "realized_pnl_usd": float(pnl), "daily_limits": row}


def run_once(*, exec_db_path: str | Path | None = None, daily_db_path: str | Path | None = None, day: str | None = None) -> Dict[str, Any]:
    return PnlHarvester(exec_db_path=exec_db_path, daily_db_path=daily_db_path).harvest(day=day)
