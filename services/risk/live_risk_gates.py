from __future__ import annotations

import logging
_LOG = logging.getLogger(__name__)

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import datetime
import sqlite3
from pathlib import Path

from services.markets.math_utils import decimal_product, decimal_value
from services.os.app_paths import data_dir, ensure_dirs

def _utc_day_key() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

@dataclass(frozen=True)
class LiveRiskLimits:
    max_daily_loss_usd: float
    max_notional_per_trade_usd: float
    max_trades_per_day: int
    max_position_notional_usd: float
    kill_switch_file: str = ""

    @staticmethod
    def from_dict(cfg: dict) -> Optional["LiveRiskLimits"]:
        risk = (cfg.get("risk") or {}).get("live") or {}
        try:
            mdl = float(
                decimal_value(risk.get("max_daily_loss_usd"), name="max_daily_loss_usd")
            )
            mnt = float(
                decimal_value(
                    risk.get("max_notional_per_trade_usd"),
                    name="max_notional_per_trade_usd",
                )
            )
            mtd_raw = decimal_value(risk.get("max_trades_per_day"), name="max_trades_per_day")
            mpn = float(
                decimal_value(
                    risk.get("max_position_notional_usd"),
                    name="max_position_notional_usd",
                )
            )
        except (ValueError, TypeError):
            return None
        if mtd_raw != mtd_raw.to_integral_value():
            return None
        mtd = int(mtd_raw)
        if not (mdl > 0 and mnt > 0 and mtd > 0 and mpn > 0):
            return None
        return LiveRiskLimits(mdl, mnt, mtd, mpn)
    @staticmethod
    def from_trading_yaml(path: str = "config/trading.yaml"):
        """Load limits from the canonical runtime trading config; fail closed if invalid."""
        import logging
        _LOG = logging.getLogger(__name__)
        try:
            from services.config_loader import load_runtime_trading_config

            data = load_runtime_trading_config(path)
            limits = LiveRiskLimits.from_dict(data)
            if limits is None:
                _LOG.critical(
                    "RISK_GATE_FAIL_CLOSED: missing_or_invalid_risk_live_limits path=%s",
                    path,
                )
            return limits
        except Exception as e:
            _LOG.critical("RISK_GATE_FAIL_CLOSED: risk_limit_load_failed:%s", type(e).__name__)
            return None

def _killswitch_file_on(path: str) -> bool:
    try:
        return Path(path).exists()
    except Exception:
        return False

# OWNERSHIP: LiveGateDB writes bot_state and daily_limits to execution.sqlite.
# This is the canonical daily_limits store for live-mode gate enforcement.
# A separate DailyLimitsSQLite (storage/daily_limits_sqlite.py) writes to
# data/daily_limits.sqlite — different file, different use case.
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

    def _estimate_notional_usd(self, it: dict) -> Optional[float]:
        v = it.get("notional_usd")
        if v is not None:
            try:
                return float(abs(decimal_value(v, name="notional_usd")))
            except ValueError:
                return None
        qty = it.get("qty")
        px = it.get("price")
        if qty is not None and px is not None:
            try:
                return float(abs(decimal_product(qty, px)))
            except ValueError:
                return None
        return None

    def _realized_pnl_usd(self, value: Any) -> Optional[float]:
        try:
            return float(decimal_value(value, name="realized_pnl_usd"))
        except ValueError:
            return None

    def check_live(self, *, it: dict, realized_pnl_usd: Any) -> Tuple[bool, str, Dict[str, Any]]:
        # KILL_SWITCH_FILE_SUPPORT
        if self.db.killswitch_on() or _killswitch_file_on(self.limits.kill_switch_file):
            return False, "KILL_SWITCH_ON", {}

        n = self._estimate_notional_usd(it)
        if n is None:
            return False, "CANNOT_ESTIMATE_NOTIONAL_USD", {}

        if n > self.limits.max_notional_per_trade_usd:
            return False, "MAX_NOTIONAL_PER_TRADE_EXCEEDED", {"notional_usd": n}

        row = self.db.day_row()
        if int(row.get("trades", 0)) >= self.limits.max_trades_per_day:
            return False, "MAX_TRADES_PER_DAY_EXCEEDED", dict(row)

        realized_pnl = self._realized_pnl_usd(realized_pnl_usd)
        if realized_pnl is None:
            return False, "CANNOT_ESTIMATE_REALIZED_PNL_USD", {}

        if realized_pnl <= -abs(self.limits.max_daily_loss_usd):
            return False, "MAX_DAILY_LOSS_EXCEEDED", {"realized_pnl_usd": realized_pnl}

        return True, "OK", {"notional_usd": n, "daily": row}


def phase83_incr_trade_counter(exec_db: str, *, gate_db: LiveGateDB | None = None, delta: int = 1) -> int:
    """Increment the Phase 83 live gate trade counter (daily_limits.trades)."""
    db = gate_db or LiveGateDB(exec_db=exec_db)
    return db.incr_trades(delta)
