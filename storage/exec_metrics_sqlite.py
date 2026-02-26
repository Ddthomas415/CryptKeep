from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "exec_metrics.sqlite"

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS exec_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  decision_id TEXT,
  intent_id TEXT,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  intended_price REAL,
  ack_ms REAL,
  fill_price REAL,
  slippage_bps REAL,
  exchange_order_id TEXT,
  status TEXT
);

CREATE INDEX IF NOT EXISTS idx_execm_ts ON exec_metrics(ts);
CREATE INDEX IF NOT EXISTS idx_execm_venue_ts ON exec_metrics(venue, ts);
CREATE INDEX IF NOT EXISTS idx_execm_symbol_ts ON exec_metrics(symbol, ts);
'''

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

class ExecMetricsSQLite:
    def __init__(self) -> None:
        _connect().close()

    def insert(self, *, decision_id: str | None, intent_id: str | None, venue: str, symbol: str, side: str,
               qty: float, intended_price: float | None, ack_ms: float | None, fill_price: float | None,
               slippage_bps: float | None, exchange_order_id: str | None, status: str | None, ts: str | None = None):
        con = _connect()
        try:
            con.execute(
                "INSERT INTO exec_metrics(ts, decision_id, intent_id, venue, symbol, side, qty, intended_price, ack_ms, fill_price, slippage_bps, exchange_order_id, status) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (str(ts or _now()), decision_id, intent_id, venue.lower().strip(), symbol.strip(), side.lower().strip(),
                 float(qty), float(intended_price) if intended_price is not None else None,
                 float(ack_ms) if ack_ms is not None else None,
                 float(fill_price) if fill_price is not None else None,
                 float(slippage_bps) if slippage_bps is not None else None,
                 exchange_order_id, status)
            )
        finally:
            con.close()

    def recent(self, venue: str | None = None, limit: int = 300) -> list[dict]:
        con = _connect()
        try:
            q = "SELECT ts, decision_id, intent_id, venue, symbol, side, qty, intended_price, ack_ms, fill_price, slippage_bps, exchange_order_id, status FROM exec_metrics"
            args = []
            if venue:
                q += " WHERE venue=?"
                args.append(venue.lower().strip())
            q += " ORDER BY ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [{"ts": r[0], "decision_id": r[1], "intent_id": r[2], "venue": r[3], "symbol": r[4],
                     "side": r[5], "qty": r[6], "intended_price": r[7], "ack_ms": r[8],
                     "fill_price": r[9], "slippage_bps": r[10], "exchange_order_id": r[11], "status": r[12]} for r in rows]
        finally:
            con.close()

    def rolling_p95(self, venue: str, window_n: int = 200) -> dict:
        rows = self.recent(venue=venue, limit=int(window_n))
        ack = sorted([float(x["ack_ms"]) for x in rows if x.get("ack_ms") is not None])
        slp = sorted([float(x["slippage_bps"]) for x in rows if x.get("slippage_bps") is not None])
        def p95(arr): return float(arr[int(max(0, round(0.95*(len(arr)-1))))]) if arr else None
        return {"venue": venue.lower().strip(), "window_n": window_n, "count_ack": len(ack), "count_slippage": len(slp),
                "ack_ms_p95": p95(ack), "slippage_bps_p95": p95(slp)}
