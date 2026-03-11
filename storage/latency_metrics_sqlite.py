from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "latency_metrics.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS latency_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_ms INTEGER NOT NULL,
  category TEXT NOT NULL,
  name TEXT NOT NULL,
  value_ms REAL NOT NULL,
  meta_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_lm_ts ON latency_metrics(ts_ms);
CREATE INDEX IF NOT EXISTS idx_lm_cat_name_ts ON latency_metrics(category, name, ts_ms);
"""


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


def _p95(values: List[float]) -> float | None:
    if not values:
        return None
    s = sorted(float(v) for v in values)
    idx = int(max(0, round(0.95 * (len(s) - 1))))
    return float(s[idx])


class LatencyMetricsSQLite:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DB_PATH
        _connect(self.path).close()

    def log_latency(self, *, ts_ms: int, category: str, name: str, value_ms: float, meta: Dict[str, Any] | None = None) -> None:
        con = _connect(self.path)
        try:
            con.execute(
                "INSERT INTO latency_metrics(ts_ms, category, name, value_ms, meta_json) VALUES(?,?,?,?,?)",
                (int(ts_ms), str(category), str(name), float(value_ms), json.dumps(meta or {}, default=str)),
            )
        finally:
            con.close()

    def recent(self, *, category: str | None = None, name: str | None = None, limit: int = 200) -> List[Dict[str, Any]]:
        q = "SELECT ts_ms, category, name, value_ms, meta_json FROM latency_metrics"
        args: list[Any] = []
        where: list[str] = []
        if category:
            where.append("category=?")
            args.append(str(category))
        if name:
            where.append("name=?")
            args.append(str(name))
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
                    meta = json.loads(r["meta_json"] or "{}")
                except Exception:
                    meta = {}
                out.append(
                    {
                        "ts_ms": int(r["ts_ms"]),
                        "category": r["category"],
                        "name": r["name"],
                        "value_ms": float(r["value_ms"]),
                        "meta": meta,
                    }
                )
            return out
        finally:
            con.close()

    def rolling_p95(self, *, category: str, name: str, window_n: int = 200) -> Dict[str, Any]:
        rows = self.recent(category=category, name=name, limit=int(window_n))
        values = [float(r["value_ms"]) for r in rows]
        return {
            "category": str(category),
            "name": str(name),
            "window_n": int(window_n),
            "count": len(values),
            "p95_ms": _p95(values),
        }
