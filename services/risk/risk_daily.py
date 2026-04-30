from __future__ import annotations

import logging
_LOG = logging.getLogger(__name__)

from dataclasses import dataclass
from typing import Any, Dict, Optional
import datetime
import sqlite3
from pathlib import Path

def _utc_day_key(now: Optional[datetime.datetime] = None) -> str:
    n = now or datetime.datetime.now(datetime.timezone.utc)
    return n.strftime("%Y-%m-%d")

def _utc_iso(now: Optional[datetime.datetime] = None) -> str:
    n = now or datetime.datetime.now(datetime.timezone.utc)
    if n.tzinfo is None:
        n = n.replace(tzinfo=datetime.timezone.utc)
    return n.isoformat().replace("+00:00", "Z")

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
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute("PRAGMA synchronous=NORMAL;")
        c.execute("PRAGMA busy_timeout=15000;")
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

            # Fill-dedupe table: prevents double-counting PnL/fees on fill replays
            c.execute("""
            CREATE TABLE IF NOT EXISTS risk_daily_fills(
              venue TEXT NOT NULL,
              fill_id TEXT NOT NULL,
              day TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY(venue, fill_id)
            );
            """)


            # Add new columns safely (SQLite needs ALTER TABLE)
            cols = {row[1] for row in c.execute("PRAGMA table_info(risk_daily)").fetchall()}
            if "notional_usd" not in cols:
                try:
                    c.execute("ALTER TABLE risk_daily ADD COLUMN notional_usd REAL NOT NULL DEFAULT 0;")
                except Exception as _err:
                    pass  # suppressed: see _LOG.debug below

    def _ensure_day_conn(self, c: sqlite3.Connection, day: str) -> None:
        c.execute(
            """
            INSERT OR IGNORE INTO risk_daily(
              day, trades, realized_pnl_usd, fees_usd, updated_at, notional_usd
            ) VALUES(?,?,?,?,?,?)
            """,
            (str(day), 0, 0.0, 0.0, _utc_iso(), 0.0),
        )

    def _get_day_conn(self, c: sqlite3.Connection, day: str) -> Dict[str, Any]:
        row = c.execute(
            "SELECT day,trades,realized_pnl_usd,fees_usd,updated_at, notional_usd FROM risk_daily WHERE day=?",
            (str(day),),
        ).fetchone()
        return dict(row) if row else {}

    def _apply_pnl_conn(
        self,
        c: sqlite3.Connection,
        *,
        day: str,
        realized_pnl_usd: float,
        fee_usd: float,
    ) -> None:
        c.execute(
            """
            UPDATE risk_daily
            SET realized_pnl_usd=realized_pnl_usd+?,
                fees_usd=fees_usd+?,
                updated_at=?
            WHERE day=?
            """,
            (float(realized_pnl_usd), float(fee_usd), _utc_iso(), str(day)),
        )

    def get(self, day: Optional[str] = None) -> Dict[str, Any]:
        d = day or _utc_day_key()
        with self._conn() as c:
            self._ensure_day_conn(c, d)
            return self._get_day_conn(c, d)

    def incr_trades(self, n: int = 1, day: Optional[str] = None) -> int:
        d = day or _utc_day_key()
        c = self._conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            self._ensure_day_conn(c, d)
            c.execute(
                "UPDATE risk_daily SET trades=trades+?, updated_at=? WHERE day=?",
                (int(n), _utc_iso(), d),
            )
            row = self._get_day_conn(c, d)
            c.execute("COMMIT")
            return int(row["trades"])
        except Exception:
            try:
                c.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            c.close()

    def add_pnl(self, realized_pnl_usd: float = 0.0, fee_usd: float = 0.0, day: Optional[str] = None) -> Dict[str, Any]:
        d = day or _utc_day_key()
        c = self._conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            self._ensure_day_conn(c, d)
            self._apply_pnl_conn(
                c,
                day=d,
                realized_pnl_usd=float(realized_pnl_usd or 0.0),
                fee_usd=float(fee_usd or 0.0),
            )
            row = self._get_day_conn(c, d)
            c.execute("COMMIT")
            return row
        except Exception:
            try:
                c.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            c.close()

    def realized_today_usd(self) -> float:
        return float(self.get(_utc_day_key()).get("realized_pnl_usd", 0.0))

    def trades_today(self) -> int:
        return int(self.get(_utc_day_key()).get("trades", 0))


    # CBP_RISK_DAILY_FILL_DEDUPE_V1
    def apply_fill_once(
        self,
        *,
        venue: str,
        fill_id: str,
        realized_pnl_usd: float = 0.0,
        fee_usd: float = 0.0,
        day: Optional[str] = None,
    ) -> bool:
        """
        Apply a fill's realized pnl + fees to today's risk_daily EXACTLY ONCE.

        Idempotency: (venue, fill_id) is recorded in risk_daily_fills with a PK constraint.
        Returns True if applied now, False if it was already applied before.
        """
        v = str(venue or "").strip().lower()
        fid = str(fill_id or "").strip()
        if not v or not fid:
            return False

        d = day or _utc_day_key()
        c = self._conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute(
                "INSERT INTO risk_daily_fills(venue, fill_id, day, created_at) VALUES(?,?,?,?)",
                (v, fid, d, _utc_iso()),
            )
            self._ensure_day_conn(c, d)
            self._apply_pnl_conn(
                c,
                day=d,
                realized_pnl_usd=float(realized_pnl_usd or 0.0),
                fee_usd=float(fee_usd or 0.0),
            )
            c.execute("COMMIT")
            return True
        except sqlite3.IntegrityError:
            try:
                c.execute("ROLLBACK")
            except Exception:
                pass
            return False
        except Exception:
            try:
                c.execute("ROLLBACK")
            except Exception:
                pass
            _LOG.exception("risk_daily.apply_fill_once_failed venue=%s fill_id=%s", v, fid)
            return False
        finally:
            c.close()

# CBP_RISK_DAILY_SNAPSHOT_V1
def _default_exec_db() -> str:
    # Prefer env
    import os
    p = os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH")
    if p:
        return str(p)
    # Try config/trading.yaml (best-effort; aligns with killswitch)
    try:
        import yaml
        from pathlib import Path as _P
        cfgp = _P("config/trading.yaml")
        if cfgp.exists():
            cfg = yaml.safe_load(cfgp.read_text(encoding="utf-8")) or {}
            ex_cfg = (cfg.get("execution") or {}) if isinstance(cfg.get("execution"), dict) else {}
            dbp = ex_cfg.get("db_path")
            if dbp:
                return str(dbp)
    except Exception as _err:
        pass  # suppressed: see _LOG.debug below
    try:
        from services.os.app_paths import data_dir, ensure_dirs
        ensure_dirs()
        return str(data_dir() / "execution.sqlite")
    except Exception:
        return "execution.sqlite"

def snapshot(exec_db: str | None = None) -> dict:
    """
    Stable snapshot for LIVE gates.
    Returns keys: day, trades, pnl, fees, realized_pnl, notional, updated_at
    pnl is net realized after fees.
    """
    db = exec_db or _default_exec_db()
    rdb = RiskDailyDB(db)
    row = rdb.get()
    realized = float(row.get("realized_pnl_usd", 0.0) or 0.0)
    fees = float(row.get("fees_usd", 0.0) or 0.0)
    notional = float(row.get("notional_usd", 0.0) or 0.0)
    return {
        "day": str(row.get("day") or ""),
        "trades": int(row.get("trades", 0) or 0),
        "realized_pnl": realized,
        "fees": fees,
        "pnl": (realized - fees),
        "notional": notional,
        "updated_at": str(row.get("updated_at") or ""),
        "exec_db": db,
    }

def record_order_attempt(notional_usd: float | None, exec_db: str | None = None) -> None:
    """
    Conservative counter: increments trades and notional on *successful submit*.
    Best-effort; should never raise (avoids retry loops after submit).
    """
    try:
        db = exec_db or _default_exec_db()
        rdb = RiskDailyDB(db)
        day = _utc_day_key()
        c = rdb._conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            rdb._ensure_day_conn(c, day)
            c.execute(
                """
                UPDATE risk_daily
                SET trades=trades+?,
                    notional_usd=notional_usd+?,
                    updated_at=?
                WHERE day=?
                """,
                (1, float(notional_usd or 0.0), _utc_iso(), day),
            )
            c.execute("COMMIT")
        except Exception:
            try:
                c.execute("ROLLBACK")
            except Exception:
                pass
        finally:
            c.close()
    except Exception:
        return
