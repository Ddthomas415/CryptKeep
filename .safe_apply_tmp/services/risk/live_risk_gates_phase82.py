from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import datetime
import sqlite3
from pathlib import Path
import yaml

def _utc_day_key() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

@dataclass(frozen=True)
class LiveRiskLimits:
    max_daily_loss_usd: float
    max_notional_per_trade_usd: float
    max_trades_per_day: int
    max_position_notional_usd: float

    @staticmethod
    def from_trading_yaml(path: str = "config/trading.yaml") -> Optional["LiveRiskLimits"]:
        p = Path(path)
        if not p.exists():
            return None
        cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        risk = (cfg.get("risk") or {}).get("live") or {}
        try:
            mdl = float(risk.get("max_daily_loss_usd"))
            mnt = float(risk.get("max_notional_per_trade_usd"))
            mtd = int(risk.get("max_trades_per_day"))
            mpn = float(risk.get("max_position_notional_usd"))
        except Exception:
            return None
        if not (mdl > 0 and mnt > 0 and mtd > 0 and mpn > 0):
            return None
        return LiveRiskLimits(mdl, mnt, mtd, mpn)

class LiveGateDB:
    def __init__(self, exec_db: str):
        self.exec_db = exec_db
        Path(exec_db).parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.exec_db, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute("PRAGMA synchronous=NORMAL;")
        return c

    def _ensure(self) -> None:
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS bot_state(k TEXT PRIMARY KEY, v TEXT NOT NULL);")
            c.execute(
                "CREATE TABLE IF NOT EXISTS daily_limits("
                "day TEXT PRIMARY KEY,"
                "trades INTEGER NOT NULL DEFAULT 0,"
                "realized_pnl_usd REAL NOT NULL DEFAULT 0,"
                "updated_at TEXT NOT NULL)"
            )

    def killswitch_on(self) -> bool:
        with self._conn() as c:
            r = c.execute("SELECT v FROM bot_state WHERE k='killswitch'").fetchone()
            return (str(r["v"]) if r else "0") == "1"

    def set_killswitch(self, on: bool) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO bot_state(k,v) VALUES('killswitch',?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                ("1" if on else "0",),
            )

    def day_row(self) -> Dict[str, Any]:
        d = _utc_day_key()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._conn() as c:
            r = c.execute("SELECT day,trades,realized_pnl_usd,updated_at FROM daily_limits WHERE day=?", (d,)).fetchone()
            if r:
                return dict(r)
            c.execute("INSERT INTO daily_limits(day,trades,realized_pnl_usd,updated_at) VALUES(?,?,?,?)", (d,0,0.0,now))
            return {"day": d, "trades": 0, "realized_pnl_usd": 0.0, "updated_at": now}

    def incr_trades(self, n: int = 1) -> int:
        d = _utc_day_key()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._conn() as c:
            r = self.day_row()
            new_val = int(r.get("trades", 0)) + int(n)
            c.execute("UPDATE daily_limits SET trades=?, updated_at=? WHERE day=?", (new_val, now, d))
            return new_val

@dataclass
class LiveRiskGates:
    limits: LiveRiskLimits
    db: LiveGateDB

    def _estimate_notional_usd(self, it: Any) -> Optional[float]:
        # intent-like object or dict
        for k in ("notional_usd", "usd_notional", "notional"):
            v = getattr(it, k, None) if not isinstance(it, dict) else it.get(k)
            if v is not None:
                try: return abs(float(v))
                except Exception: pass
        qty = getattr(it, "qty", None) if not isinstance(it, dict) else it.get("qty")
        px  = getattr(it, "price", None) if not isinstance(it, dict) else it.get("price")
        if qty is not None and px is not None:
            try: return abs(float(qty) * float(px))
            except Exception: return None
        return None

    def check_live(self, *, it: Any, realized_pnl_usd: float) -> Tuple[bool, str, Dict[str, Any]]:
        if self.db.killswitch_on():
            return False, "KILL_SWITCH_ON", {}
        n = self._estimate_notional_usd(it)
        if n is None:
            return False, "CANNOT_ESTIMATE_NOTIONAL_USD", {}
        if n > self.limits.max_notional_per_trade_usd:
            return False, "MAX_NOTIONAL_PER_TRADE_EXCEEDED", {"notional_usd": n}
        row = self.db.day_row()
        if int(row.get("trades", 0)) >= self.limits.max_trades_per_day:
            return False, "MAX_TRADES_PER_DAY_EXCEEDED", dict(row)
        if float(realized_pnl_usd) <= -abs(self.limits.max_daily_loss_usd):
            return False, "MAX_DAILY_LOSS_EXCEEDED", {"realized_pnl_usd": float(realized_pnl_usd)}
        return True, "OK", {"notional_usd": n, "daily": row}
