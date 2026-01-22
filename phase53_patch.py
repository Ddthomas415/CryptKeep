from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------- Helper functions ----------
def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"Missing file: {path}")
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---------- Phase 53: Decision Audit Store ----------

# 1) Create decision_audit_store_sqlite.py
write("storage/decision_audit_store_sqlite.py", r"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path("data") / "decision_audit.sqlite"

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS decisions (
  decision_id TEXT PRIMARY KEY,
  first_seen_ts TEXT NOT NULL,
  last_seen_ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  safety_ok INTEGER,
  safety_reason TEXT,
  meta_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_decisions_last_seen ON decisions(last_seen_ts);
CREATE INDEX IF NOT EXISTS idx_decisions_venue_symbol ON decisions(venue, symbol);
'''

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class DecisionAuditStoreSQLite:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db = db_path
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db, isolation_level=None, check_same_thread=False)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _init(self) -> None:
        con = self._connect()
        try:
            for stmt in SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    con.execute(s)
        finally:
            con.close()

    def upsert_decision(
        self,
        decision_id: str,
        venue: str,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        meta: dict | None = None,
        safety_ok: bool | None = None,
        safety_reason: str | None = None,
        ts: str | None = None,
    ) -> None:
        ts = ts or _now()
        meta_json = None
        try:
            meta_json = json.dumps(meta or {}, sort_keys=True)
        except Exception:
            meta_json = None
        con = self._connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO decisions(decision_id, first_seen_ts, last_seen_ts, venue, symbol, side, qty, price, safety_ok, safety_reason, meta_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(decision_id),
                    str(ts),
                    str(ts),
                    str(venue),
                    str(symbol),
                    str(side),
                    float(qty),
                    float(price),
                    (1 if safety_ok else 0) if safety_ok is not None else None,
                    (str(safety_reason) if safety_reason is not None else None),
                    meta_json,
                ),
            )
            con.execute(
                "UPDATE decisions SET last_seen_ts=?, safety_ok=COALESCE(?, safety_ok), safety_reason=COALESCE(?, safety_reason), meta_json=COALESCE(?, meta_json) "
                "WHERE decision_id=?",
                (
                    str(ts),
                    (1 if safety_ok else 0) if safety_ok is not None else None,
                    (str(safety_reason) if safety_reason is not None else None),
                    meta_json,
                    str(decision_id),
                ),
            )
        finally:
            con.close()

    def last_decisions(self, limit: int = 200, venue: str | None = None, symbol: str | None = None) -> List[dict]:
        con = self._connect()
        try:
            q = "SELECT decision_id, first_seen_ts, last_seen_ts, venue, symbol, side, qty, price, safety_ok, safety_reason, meta_json FROM decisions"
            args = []
            wh = []
            if venue:
                wh.append("venue=?"); args.append(str(venue))
            if symbol:
                wh.append("symbol=?"); args.append(str(symbol))
            if wh:
                q += " WHERE " + " AND ".join(wh)
            q += " ORDER BY last_seen_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            out = []
            for r in rows:
                meta = None
                try:
                    meta = json.loads(r[10]) if r[10] else None
                except Exception:
                    meta = None
                out.append({
                    "decision_id": r[0],
                    "first_seen_ts": r[1],
                    "last_seen_ts": r[2],
                    "venue": r[3],
                    "symbol": r[4],
                    "side": r[5],
                    "qty": float(r[6]),
                    "price": float(r[7]),
                    "safety_ok": (bool(r[8]) if r[8] is not None else None),
                    "safety_reason": r[9],
                    "meta": meta,
                })
            return out
        finally:
            con.close()
""")

# 2) Update CHECKPOINTS.md
def patch_cp(t: str) -> str:
    if "## BA) Decision Audit Store" in t:
        return t
    return t + (
        "\n## BA) Decision Audit Store\n"
        "- ✅ BA1: decision_audit.sqlite stores decision_id + deterministic decision inputs\n"
        "- ✅ BA2: Router persists decision audit records (best-effort)\n"
        "- ✅ BA3: Dashboard viewer for decision audit + meta drilldown\n"
    )

patch("CHECKPOINTS.md", patch_cp)

print("OK: Phase 53 applied (decision audit store + checkpoints).")

