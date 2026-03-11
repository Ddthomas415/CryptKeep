from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "execution_report.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS execution_reports (
  report_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  ts_ms INTEGER NOT NULL,
  venue TEXT,
  symbol TEXT,
  status TEXT,
  summary TEXT,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_er_ts_ms ON execution_reports(ts_ms);
CREATE INDEX IF NOT EXISTS idx_er_venue_symbol ON execution_reports(venue, symbol);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con


class ExecutionReportSQLite:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DB_PATH
        _connect(self.path).close()

    def add_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        rid = str(report.get("report_id") or report.get("id") or "")
        if not rid:
            raise ValueError("report_id is required")
        row = (
            rid,
            str(report.get("ts") or _now_iso()),
            int(report.get("ts_ms") or _now_ms()),
            None if report.get("venue") is None else str(report.get("venue")),
            None if report.get("symbol") is None else str(report.get("symbol")),
            None if report.get("status") is None else str(report.get("status")),
            None if report.get("summary") is None else str(report.get("summary")),
            json.dumps(report.get("payload") or report, default=str),
        )
        con = _connect(self.path)
        try:
            con.execute(
                "INSERT OR REPLACE INTO execution_reports(report_id, ts, ts_ms, venue, symbol, status, summary, payload_json) VALUES(?,?,?,?,?,?,?,?)",
                row,
            )
        finally:
            con.close()
        return {"ok": True, "report_id": rid}

    def recent(self, *, limit: int = 200, venue: str | None = None, symbol: str | None = None) -> List[Dict[str, Any]]:
        q = "SELECT report_id, ts, ts_ms, venue, symbol, status, summary, payload_json FROM execution_reports"
        args: list[Any] = []
        where: list[str] = []
        if venue:
            where.append("venue=?")
            args.append(str(venue))
        if symbol:
            where.append("symbol=?")
            args.append(str(symbol))
        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY ts_ms DESC LIMIT ?"
        args.append(int(limit))
        con = _connect(self.path)
        try:
            rows = con.execute(q, tuple(args)).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                try:
                    payload = json.loads(r["payload_json"] or "{}")
                except Exception:
                    payload = {}
                out.append(
                    {
                        "report_id": r["report_id"],
                        "ts": r["ts"],
                        "ts_ms": int(r["ts_ms"]),
                        "venue": r["venue"],
                        "symbol": r["symbol"],
                        "status": r["status"],
                        "summary": r["summary"],
                        "payload": payload,
                    }
                )
            return out
        finally:
            con.close()

    def latest(self, *, venue: str | None = None, symbol: str | None = None) -> Dict[str, Any] | None:
        rows = self.recent(limit=1, venue=venue, symbol=symbol)
        return rows[0] if rows else None
