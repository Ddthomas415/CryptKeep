from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "risk_ledger.sqlite"

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS positions (
  run_id TEXT,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  qty REAL NOT NULL,
  avg_cost REAL NOT NULL,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (venue, symbol)
);

CREATE TABLE IF NOT EXISTS daily_venue (
  run_id TEXT,
  day TEXT NOT NULL,
  venue TEXT NOT NULL,
  trades_count INTEGER NOT NULL,
  notional_usd REAL NOT NULL,
  realized_pnl_usd REAL NOT NULL,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (day, venue)
);

CREATE INDEX IF NOT EXISTS idx_daily_venue_day ON daily_venue(day);
CREATE INDEX IF NOT EXISTS idx_daily_venue_venue ON daily_venue(venue);

CREATE TABLE IF NOT EXISTS daily (
  run_id TEXT,
  day TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  trades_count INTEGER NOT NULL,
  notional_usd REAL NOT NULL,
  realized_pnl_usd REAL NOT NULL,
  updated_ts TEXT NOT NULL,
  PRIMARY KEY (day, venue, symbol)
);

CREATE INDEX IF NOT EXISTS idx_daily_day ON daily(day);
CREATE INDEX IF NOT EXISTS idx_daily_venue ON daily(venue);
'''

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class RiskLedgerStoreSQLite:
    def __init__(self, db_path: Path = DB_PATH):
        self.db = db_path
        self._init()

    def _init(self):
        con = _connect()
        con.close()

    
    def get_daily_venue(self, day: str, venue: str) -> dict:
        con = _connect()
        try:
            r = con.execute(
                "SELECT trades_count, notional_usd, realized_pnl_usd, updated_ts FROM daily_venue WHERE day=? AND venue=?",
                (str(day), str(venue)),
            ).fetchone()
            if not r:
                return {"day": day, "venue": venue, "trades_count": 0, "notional_usd": 0.0, "realized_pnl_usd": 0.0, "updated_ts": None}
            return {"day": day, "venue": venue, "trades_count": int(r[0]), "notional_usd": float(r[1]), "realized_pnl_usd": float(r[2]), "updated_ts": r[3]}
        finally:
            con.close()

    def upsert_daily_venue(self, day: str, venue: str, trades_count: int, notional_usd: float, realized_pnl_usd: float, run_id: str | None = None) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT INTO daily_venue(run_id, day, venue, trades_count, notional_usd, realized_pnl_usd, updated_ts) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(day, venue) DO UPDATE SET run_id=excluded.run_id, trades_count=excluded.trades_count, notional_usd=excluded.notional_usd, realized_pnl_usd=excluded.realized_pnl_usd, updated_ts=excluded.updated_ts",
                (run_id, str(day), str(venue), int(trades_count), float(notional_usd), float(realized_pnl_usd), _now()),
            )
        finally:
            con.close()

def get_daily(self, day: str, venue: str, symbol: str) -> dict:
        con = _connect()
        try:
            r = con.execute(
                "SELECT trades_count, notional_usd, realized_pnl_usd, updated_ts FROM daily WHERE day=? AND venue=? AND symbol=?",
                (str(day), str(venue), str(symbol))
            ).fetchone()
            if not r:
                return {
                    "day": day,
                    "venue": venue,
                    "symbol": symbol,
                    "trades_count": 0,
                    "notional_usd": 0.0,
                    "realized_pnl_usd": 0.0,
                    "updated_ts": None
                }
            return {
                "day": day,
                "venue": venue,
                "symbol": symbol,
                "trades_count": int(r[0]),
                "notional_usd": float(r[1]),
                "realized_pnl_usd": float(r[2]),
                "updated_ts": r[3]
            }
        finally:
            con.close()
