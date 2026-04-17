from __future__ import annotations

import logging
_LOG = logging.getLogger(__name__)

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple
import datetime
import sqlite3
from pathlib import Path

def _utc_day_bounds(day: Optional[str] = None) -> Tuple[datetime.datetime, datetime.datetime]:
    if day is None:
        day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    start = datetime.datetime.fromisoformat(day + "T00:00:00")
    end = start + datetime.timedelta(days=1)
    return start, end

def _parse_ts(v: Any) -> Optional[datetime.datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        x = float(v)
        if x > 1e12:
            x = x / 1000.0
        try:
            return datetime.datetime.utcfromtimestamp(x)
        except Exception:
            return None
    s = str(v).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1]
    try:
        return datetime.datetime.fromisoformat(s.replace(" ", "T"))
    except Exception:
        return None

def _conn(exec_db: str) -> sqlite3.Connection:
    Path(exec_db).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(exec_db)
    c.row_factory = sqlite3.Row
    return c

def _tables(c: sqlite3.Connection) -> List[str]:
    rows = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return [str(r["name"]) for r in rows]

def _cols(c: sqlite3.Connection, table: str) -> List[str]:
    rows = c.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(r["name"]) for r in rows]

def _pick_first(existing: Sequence[str], options: Sequence[str]) -> Optional[str]:
    s = {x.lower(): x for x in existing}
    for o in options:
        if o.lower() in s:
            return s[o.lower()]
    return None

@dataclass
class JournalSignals:
    exec_db: str

    def realized_pnl_today_usd(self) -> Optional[float]:
        with _conn(self.exec_db) as c:
            tbls = _tables(c)
            day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

            # Prefer Phase 82 table
            if "daily_limits" in tbls:
                r = c.execute("SELECT realized_pnl_usd FROM daily_limits WHERE day = ?", (day,)).fetchone()
                if r is not None and r["realized_pnl_usd"] is not None:
                    try:
                        return float(r["realized_pnl_usd"])
                    except Exception as _err:
                        pass  # suppressed: see _LOG.debug below

            # Fallback: sum PnL from fills-like tables if ts+pnl cols exist
            candidates = [t for t in tbls if t.lower() in ("fills", "executions", "trades", "trade_fills")]
            start, end = _utc_day_bounds(day)
            for t in candidates:
                cols = _cols(c, t)
                pnl_col = _pick_first(cols, ["realized_pnl_usd", "pnl_usd", "realized_pnl", "pnl"])
                ts_col  = _pick_first(cols, ["ts", "timestamp", "filled_at", "created_at", "executed_at", "time"])
                if not (pnl_col and ts_col):
                    continue
                rows = c.execute(f"SELECT {pnl_col} AS pnl, {ts_col} AS ts FROM {t}").fetchall()
                total = 0.0
                any_rows = False
                for r in rows:
                    if r["pnl"] is None:
                        continue
                    ts = _parse_ts(r["ts"])
                    if ts is None or not (start <= ts < end):
                        continue
                    try:
                        total += float(r["pnl"])
                        any_rows = True
                    except Exception as _err:
                        pass  # suppressed: see _LOG.debug below
                if any_rows:
                    return float(total)

        return None

    def trades_today(self) -> Optional[int]:
        with _conn(self.exec_db) as c:
            tbls = _tables(c)
            day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

            if "daily_limits" in tbls:
                r = c.execute("SELECT trades FROM daily_limits WHERE day = ?", (day,)).fetchone()
                if r is not None and r["trades"] is not None:
                    try:
                        return int(r["trades"])
                    except Exception as _err:
                        pass  # suppressed: see _LOG.debug below

            candidates = [t for t in tbls if t.lower() in ("orders", "fills", "executions", "trades")]
            start, end = _utc_day_bounds(day)
            for t in candidates:
                cols = _cols(c, t)
                ts_col = _pick_first(cols, ["ts", "timestamp", "created_at", "filled_at", "executed_at", "time"])
                if not ts_col:
                    continue
                rows = c.execute(f"SELECT {ts_col} AS ts FROM {t}").fetchall()
                n = 0
                for r in rows:
                    ts = _parse_ts(r["ts"])
                    if ts is not None and (start <= ts < end):
                        n += 1
                if n > 0:
                    return int(n)

        return None
