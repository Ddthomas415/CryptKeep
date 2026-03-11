from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from services.ai_engine.features import build_feature_map
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "feature_store.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS feature_rows (
  row_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  symbol TEXT,
  side TEXT,
  features_json TEXT NOT NULL,
  label INTEGER
);
CREATE INDEX IF NOT EXISTS idx_fr_ts ON feature_rows(ts);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


class FeatureStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DB_PATH
        _connect(self.path).close()

    def add_context(
        self,
        *,
        row_id: str,
        context: Dict[str, Any],
        symbol: str | None = None,
        side: str | None = None,
        label: int | None = None,
    ) -> Dict[str, Any]:
        import json

        fmap = build_feature_map(context)
        con = _connect(self.path)
        try:
            con.execute(
                "INSERT OR REPLACE INTO feature_rows(row_id, ts, symbol, side, features_json, label) VALUES(?,?,?,?,?,?)",
                (
                    str(row_id),
                    _now(),
                    None if symbol is None else str(symbol),
                    None if side is None else str(side),
                    json.dumps(fmap, sort_keys=True),
                    None if label is None else int(label),
                ),
            )
        finally:
            con.close()
        return {"ok": True, "row_id": str(row_id), "feature_count": len(fmap)}

    def recent(self, *, limit: int = 200) -> List[Dict[str, Any]]:
        import json

        con = _connect(self.path)
        try:
            rows = con.execute(
                "SELECT row_id, ts, symbol, side, features_json, label FROM feature_rows ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                try:
                    feats = json.loads(r["features_json"] or "{}")
                except Exception:
                    feats = {}
                out.append(
                    {
                        "row_id": r["row_id"],
                        "ts": r["ts"],
                        "symbol": r["symbol"],
                        "side": r["side"],
                        "features": feats,
                        "label": r["label"],
                    }
                )
            return out
        finally:
            con.close()
