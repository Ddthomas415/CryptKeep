from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import datetime
import sqlite3
from pathlib import Path
import yaml
from services.risk.risk_daily import RiskDailyDB  # Phase 85

def _utc_day_key(now: Optional[datetime.datetime] = None) -> str:
    n = now or datetime.datetime.utcnow()
    return n.strftime("%Y-%m-%d")

def _utc_iso(now: Optional[datetime.datetime] = None) -> str:
    n = now or datetime.datetime.utcnow()
    return n.isoformat() + "Z"

def _load_yaml(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

@dataclass(frozen=True)
class LiveRiskLimits:
    max_daily_loss_usd: float
    max_notional_per_trade_usd: float
    max_trades_per_day: int
    max_position_notional_usd: float

    @staticmethod
    def from_trading_yaml(path: str = "config/trading.yaml") -> Optional["LiveRiskLimits"]:
        cfg = _load_yaml(path)
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
    """
    Minimal state storage in exec_db (SQLite):
      - bot_state: key/value (killswitch)
      - daily_limits: trades + realized_pnl_usd (best-effort rollup)
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
            CREATE TABLE IF NOT EXISTS bot_state(
              k TEXT PRIMARY KEY,
              v TEXT NOT NULL
            );
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS daily_limits(
              day TEXT PRIMARY KEY,
              trades INTEGER NOT NULL DEFAULT 0,
              realized_pnl_usd REAL NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL
            );
            """)

    def get_state(self, key: str, default: str = "") -> str:
        with self._conn() as c:
            r = c.execute("SELECT v FROM bot_state WHERE k = ?", (key,)).fetchone()
            return str(r["v"]) if r else default

    def set_state(self, key: str, value: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO bot_state(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                (key, value),
            )

    def killswitch_on(self) -> bool:
        return self.get_state("killswitch", "0") == "1"

    def set_killswitch(self, on: bool) -> None:
        self.set_state("killswitch", "1" if on else "0")

    def day_row(self, day: Optional[str] = None) -> Dict[str, Any]:
        d = day or _utc_day_key()
        with self._conn() as c:
            r = c.execute("SELECT day,trades,realized_pnl_usd,updated_at FROM daily_limits WHERE day = ?", (d,)).fetchone()
            if r:
                return dict(r)
            c.execute(
                "INSERT INTO daily_limits(day,trades,realized_pnl_usd,updated_at) VALUES(?,?,?,?)",
                (d, 0, 0.0, _utc_iso())
            )
            return {"day": d, "trades": 0, "realized_pnl_usd": 0.0, "updated_at": _utc_iso()}

    def incr_trades(self, n: int = 1, day: Optional[str] = None) -> int:
        d = day or _utc_day_key()
        with self._conn() as c:
            row = self.day_row(d)
            new_val = int(row["trades"]) + int(n)
            c.execute("UPDATE daily_limits SET trades=?, updated_at=? WHERE day=?", (new_val, _utc_iso(), d))
            return new_val

    def set_realized_pnl(self, pnl_usd: float, day: Optional[str] = None) -> None:
        d = day or _utc_day_key()
        with self._conn() as c:
            self.day_row(d)
            c.execute("UPDATE daily_limits SET realized_pnl_usd=?, updated_at=? WHERE day=?", (float(pnl_usd), _utc_iso(), d))

@dataclass
class LiveRiskGates:
    limits: LiveRiskLimits
    db: LiveGateDB

    def _estimate_notional_usd(self, intent: Any) -> Optional[float]:
        # fail-closed: if we can't estimate, LIVE blocks
        # Supports attrs or dict keys: notional_usd/usd_notional/notional or qty*price.
        def get(k: str):
            if isinstance(intent, dict):
                return intent.get(k)
            return getattr(intent, k, None)

        for k in ("notional_usd", "usd_notional", "notional"):
            v = get(k)
            if v is not None:
                try:
                    return abs(float(v))
                except Exception:
                    pass
        qty = get("qty") or get("size") or get("delta_qty")
        px = get("price") or get("mark_price") or get("ref_price")
        if qty is not None and px is not None:
            try:
                return abs(float(qty) * float(px))
            except Exception:
                return None
        return None

    def check_live(self, *, intent: Any, realized_pnl_usd: Optional[float]) -> Tuple[bool, str, Dict[str, Any]]:
        if self.db.killswitch_on():
            return (False, "KILL_SWITCH_ON", {"killswitch": True})

        notional = self._estimate_notional_usd(intent)
        if notional is None:
            return (False, "CANNOT_ESTIMATE_NOTIONAL_USD", {"hint": "intent missing notional_usd or qty+price"})

        if notional > self.limits.max_notional_per_trade_usd:
            return (False, "MAX_NOTIONAL_PER_TRADE_EXCEEDED", {"notional_usd": notional, "limit": self.limits.max_notional_per_trade_usd})

        day = _utc_day_key()
        # Phase 85: use risk_daily as the single source of truth
        rd = RiskDailyDB(self.db.exec_db).get(day)
        trades_today = int(rd.get('trades', 0))if trades_today >= self.limits.max_trades_per_day:
            return (False, "MAX_TRADES_PER_DAY_EXCEEDED", {"trades_today": trades_today, "limit": self.limits.max_trades_per_day})

        # fail-closed: LIVE requires a daily PnL source
        if realized_pnl_usd is None:
            return (False, "DAILY_PNL_UNKNOWN_BLOCK_LIVE", {"hint": "wire daily PnL source or Phase 83 risk_daily"})

        if float(realized_pnl_usd) <= -abs(self.limits.max_daily_loss_usd):
            return (False, "MAX_DAILY_LOSS_EXCEEDED", {"realized_pnl_usd": float(realized_pnl_usd), "limit": self.limits.max_daily_loss_usd})

        return (True, "OK", {"intent_notional_usd": float(notional), "trades_today": trades_today, "realized_pnl_usd": float(realized_pnl_usd)})

# PHASE85_RISK_DAILY_UNIFIED
