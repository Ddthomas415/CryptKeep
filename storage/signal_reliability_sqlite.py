from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "signal_reliability.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS signal_reliability (
  id TEXT PRIMARY KEY,
  updated_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  author TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  horizon_candles INTEGER NOT NULL,
  threshold_bps REAL NOT NULL,
  n_signals INTEGER NOT NULL,
  n_scored INTEGER NOT NULL,
  hit_rate REAL NOT NULL,
  avg_return_bps REAL NOT NULL,
  avg_abs_return_bps REAL NOT NULL,
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_sr_key ON signal_reliability(source, author, symbol, venue, timeframe, horizon_candles);
CREATE INDEX IF NOT EXISTS idx_sr_updated ON signal_reliability(updated_ts);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class SignalReliabilitySQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO signal_reliability("
                "id, updated_ts, source, author, symbol, venue, timeframe, horizon_candles, threshold_bps,"
                "n_signals, n_scored, hit_rate, avg_return_bps, avg_abs_return_bps, notes"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["id"]),
                    str(row.get("updated_ts") or _now()),
                    str(row["source"]),
                    str(row["author"]),
                    str(row["symbol"]),
                    str(row["venue"]),
                    str(row["timeframe"]),
                    int(row["horizon_candles"]),
                    float(row["threshold_bps"]),
                    int(row["n_signals"]),
                    int(row["n_scored"]),
                    float(row["hit_rate"]),
                    float(row["avg_return_bps"]),
                    float(row["avg_abs_return_bps"]),
                    str(row.get("notes") or ""),
                ),
            )
        finally:
            con.close()

    def list(self, limit: int = 500, symbol: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT id, updated_ts, source, author, symbol, venue, timeframe, horizon_candles, threshold_bps, "
                 "n_signals, n_scored, hit_rate, avg_return_bps, avg_abs_return_bps, notes "
                 "FROM signal_reliability")
            args = []
            if symbol:
                q += " WHERE symbol=?"
                args.append(str(symbol))
            q += " ORDER BY updated_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "id": r[0], "updated_ts": r[1], "source": r[2], "author": r[3], "symbol": r[4],
                    "venue": r[5], "timeframe": r[6], "horizon_candles": r[7], "threshold_bps": r[8],
                    "n_signals": r[9], "n_scored": r[10], "hit_rate": r[11], "avg_return_bps": r[12],
                    "avg_abs_return_bps": r[13], "notes": r[14],
                }
                for r in rows
            ]
        finally:
            con.close()

    def get_one(self, *, source: str, author: str, symbol: str, venue: str, timeframe: str, horizon_candles: int) -> Dict[str, Any] | None:
        con = _connect()
        try:
            r = con.execute(
                "SELECT id, updated_ts, source, author, symbol, venue, timeframe, horizon_candles, threshold_bps, "
                "n_signals, n_scored, hit_rate, avg_return_bps, avg_abs_return_bps, notes "
                "FROM signal_reliability WHERE source=? AND author=? AND symbol=? AND venue=? AND timeframe=? AND horizon_candles=? "
                "ORDER BY updated_ts DESC LIMIT 1",
                (str(source), str(author), str(symbol), str(venue), str(timeframe), int(horizon_candles)),
            ).fetchone()
            if not r:
                return None
            return {
                "id": r[0], "updated_ts": r[1], "source": r[2], "author": r[3], "symbol": r[4],
                "venue": r[5], "timeframe": r[6], "horizon_candles": r[7], "threshold_bps": r[8],
                "n_signals": r[9], "n_scored": r[10], "hit_rate": r[11], "avg_return_bps": r[12],
                "avg_abs_return_bps": r[13], "notes": r[14],
            }
        finally:
            con.close()
