from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data") / "risk_blocks.sqlite"

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS risk_blocks (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  decision_id TEXT,
  ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT,
  qty REAL,
  price REAL,
  gate TEXT,
  reason TEXT,
  details_json TEXT,
  risk_config_json TEXT,
  ledger_json TEXT,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_rb_ts ON risk_blocks(ts);
CREATE INDEX IF NOT EXISTS idx_rb_run ON risk_blocks(run_id);
CREATE INDEX IF NOT EXISTS idx_rb_decision ON risk_blocks(decision_id);
CREATE INDEX IF NOT EXISTS idx_rb_venue ON risk_blocks(venue);
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

class RiskBlocksStoreSQLite:
    def __init__(self) -> None:
        _connect().close()

    def insert(self, rec: dict) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO risk_blocks(id, run_id, decision_id, ts, venue, symbol, side, qty, price, gate, reason, details_json, risk_config_json, ledger_json, meta_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(rec.get("id")),
                    rec.get("run_id"),
                    rec.get("decision_id"),
                    str(rec.get("ts") or _now()),
                    str(rec.get("venue")),
                    str(rec.get("symbol")),
                    rec.get("side"),
                    float(rec.get("qty") or 0.0),
                    float(rec.get("price") or 0.0),
                    rec.get("gate"),
                    rec.get("reason"),
                    json.dumps(rec.get("details") or {}, sort_keys=True),
                    json.dumps(rec.get("risk_config") or {}, sort_keys=True),
                    json.dumps(rec.get("ledger") or {}, sort_keys=True),
                    json.dumps(rec.get("meta") or {}, sort_keys=True),
                )
            )
        finally:
            con.close()

    def last_n(self, limit: int = 200, run_id: str | None = None, venue: str | None = None, gate: str | None = None) -> list[dict]:
        con = _connect()
        try:
            q = "SELECT id, run_id, decision_id, ts, venue, symbol, side, qty, price, gate, reason, details_json, risk_config_json, ledger_json, meta_json FROM risk_blocks"
            args = []
            wh = []
            if run_id:
                wh.append("run_id=?"); args.append(str(run_id))
            if venue:
                wh.append("venue=?"); args.append(str(venue))
            if gate:
                wh.append("gate=?"); args.append(str(gate))
            if wh:
                q += " WHERE " + " AND ".join(wh)
            q += " ORDER BY ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            out = []
            for r in rows:
                def j(x):
                    try: return json.loads(x) if x else {}
                    except Exception: return {}
                out.append({
                    "id": r[0], "run_id": r[1], "decision_id": r[2], "ts": r[3],
                    "venue": r[4], "symbol": r[5], "side": r[6], "qty": r[7], "price": r[8],
                    "gate": r[9], "reason": r[10],
                    "details": j(r[11]), "risk_config": j(r[12]), "ledger": j(r[13]), "meta": j(r[14]),
                })
            return out
        finally:
            con.close()
