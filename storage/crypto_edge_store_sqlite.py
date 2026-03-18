from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from services.analytics.crypto_edges import build_crypto_edge_report
from services.os.app_paths import data_dir, ensure_dirs

DB_PATH = data_dir() / "crypto_edge_research.sqlite"


DDL = """
CREATE TABLE IF NOT EXISTS funding_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id TEXT NOT NULL,
  capture_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  funding_rate REAL NOT NULL,
  interval_hours REAL NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_funding_snapshots_capture_ts
  ON funding_snapshots(capture_ts DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_funding_snapshots_snapshot_id
  ON funding_snapshots(snapshot_id, id);

CREATE TABLE IF NOT EXISTS basis_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id TEXT NOT NULL,
  capture_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  spot_px REAL NOT NULL,
  perp_px REAL NOT NULL,
  days_to_expiry REAL,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_basis_snapshots_capture_ts
  ON basis_snapshots(capture_ts DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_basis_snapshots_snapshot_id
  ON basis_snapshots(snapshot_id, id);

CREATE TABLE IF NOT EXISTS quote_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id TEXT NOT NULL,
  capture_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  bid REAL,
  ask REAL,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_quote_snapshots_capture_ts
  ON quote_snapshots(capture_ts DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_quote_snapshots_snapshot_id
  ON quote_snapshots(snapshot_id, id);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _s(value: Any) -> str:
    return str(value or "").strip()


def _snapshot_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@dataclass
class CryptoEdgeStoreSQLite:
    path: str = ""

    def __post_init__(self) -> None:
        if not self.path:
            ensure_dirs()
            self.path = str(DB_PATH)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        db_path = Path(self.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(DDL)
            conn.commit()

    def append_funding_rows(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        source: str = "manual",
        capture_ts: str | None = None,
        snapshot_id: str | None = None,
        interval_hours: float = 8.0,
    ) -> str:
        snap_id = str(snapshot_id or _snapshot_id("funding"))
        ts = str(capture_ts or _now_iso())
        items = [dict(row or {}) for row in list(rows or [])]
        with self._connect() as conn:
            for row in items:
                payload = {
                    "symbol": _s(row.get("symbol")),
                    "venue": _s(row.get("venue")),
                    "funding_rate": _fnum(row.get("funding_rate"), 0.0),
                    "interval_hours": _fnum(row.get("interval_hours"), interval_hours),
                }
                conn.execute(
                    """
                    INSERT INTO funding_snapshots(
                      snapshot_id, capture_ts, source, symbol, venue, funding_rate, interval_hours, payload_json
                    ) VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        snap_id,
                        ts,
                        str(source or "manual"),
                        payload["symbol"],
                        payload["venue"],
                        payload["funding_rate"],
                        payload["interval_hours"],
                        json.dumps(payload, default=str),
                    ),
                )
            conn.commit()
        return snap_id

    def append_basis_rows(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        source: str = "manual",
        capture_ts: str | None = None,
        snapshot_id: str | None = None,
    ) -> str:
        snap_id = str(snapshot_id or _snapshot_id("basis"))
        ts = str(capture_ts or _now_iso())
        items = [dict(row or {}) for row in list(rows or [])]
        with self._connect() as conn:
            for row in items:
                payload = {
                    "symbol": _s(row.get("symbol")),
                    "venue": _s(row.get("venue")),
                    "spot_px": _fnum(row.get("spot_px"), 0.0),
                    "perp_px": _fnum(row.get("perp_px"), 0.0),
                    "days_to_expiry": row.get("days_to_expiry"),
                }
                conn.execute(
                    """
                    INSERT INTO basis_snapshots(
                      snapshot_id, capture_ts, source, symbol, venue, spot_px, perp_px, days_to_expiry, payload_json
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        snap_id,
                        ts,
                        str(source or "manual"),
                        payload["symbol"],
                        payload["venue"],
                        payload["spot_px"],
                        payload["perp_px"],
                        payload["days_to_expiry"],
                        json.dumps(payload, default=str),
                    ),
                )
            conn.commit()
        return snap_id

    def append_quote_rows(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        source: str = "manual",
        capture_ts: str | None = None,
        snapshot_id: str | None = None,
    ) -> str:
        snap_id = str(snapshot_id or _snapshot_id("quotes"))
        ts = str(capture_ts or _now_iso())
        items = [dict(row or {}) for row in list(rows or [])]
        with self._connect() as conn:
            for row in items:
                payload = {
                    "symbol": _s(row.get("symbol")),
                    "venue": _s(row.get("venue")),
                    "bid": row.get("bid"),
                    "ask": row.get("ask"),
                }
                conn.execute(
                    """
                    INSERT INTO quote_snapshots(
                      snapshot_id, capture_ts, source, symbol, venue, bid, ask, payload_json
                    ) VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        snap_id,
                        ts,
                        str(source or "manual"),
                        payload["symbol"],
                        payload["venue"],
                        payload["bid"],
                        payload["ask"],
                        json.dumps(payload, default=str),
                    ),
                )
            conn.commit()
        return snap_id

    def _latest_snapshot_rows(self, table: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT snapshot_id, capture_ts, source FROM {table} ORDER BY capture_ts DESC, id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return []
            rows = conn.execute(
                f"SELECT payload_json FROM {table} WHERE snapshot_id = ? ORDER BY id ASC",
                (str(row["snapshot_id"]),),
            ).fetchall()
        return [dict(json.loads(str(item["payload_json"]))) for item in rows]

    def latest_funding_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("funding_snapshots")

    def latest_basis_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("basis_snapshots")

    def latest_quote_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("quote_snapshots")

    def _latest_snapshot_meta(self, table: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT snapshot_id, capture_ts, source, COUNT(*) AS row_count FROM {table} "
                "GROUP BY snapshot_id, capture_ts, source "
                "ORDER BY capture_ts DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return {
            "snapshot_id": str(row["snapshot_id"]),
            "capture_ts": str(row["capture_ts"]),
            "source": str(row["source"]),
            "row_count": int(row["row_count"] or 0),
        }

    def _recent_snapshot_meta(self, table: str, *, kind: str, limit: int = 5) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT snapshot_id, capture_ts, source, COUNT(*) AS row_count FROM {table} "
                "GROUP BY snapshot_id, capture_ts, source "
                "ORDER BY capture_ts DESC LIMIT ?",
                (int(max(limit, 1)),),
            ).fetchall()
        return [
            {
                "kind": str(kind),
                "snapshot_id": str(row["snapshot_id"]),
                "capture_ts": str(row["capture_ts"]),
                "source": str(row["source"]),
                "row_count": int(row["row_count"] or 0),
            }
            for row in rows
        ]

    def recent_snapshot_history(self, *, limit_per_kind: int = 5) -> list[dict[str, Any]]:
        rows = (
            self._recent_snapshot_meta("funding_snapshots", kind="funding", limit=limit_per_kind)
            + self._recent_snapshot_meta("basis_snapshots", kind="basis", limit=limit_per_kind)
            + self._recent_snapshot_meta("quote_snapshots", kind="quotes", limit=limit_per_kind)
        )
        rows.sort(key=lambda row: str(row.get("capture_ts") or ""), reverse=True)
        return rows

    def latest_report(self) -> dict[str, Any]:
        funding_rows = self.latest_funding_rows()
        basis_rows = self.latest_basis_rows()
        quote_rows = self.latest_quote_rows()
        report = build_crypto_edge_report(
            funding_rows=funding_rows,
            basis_rows=basis_rows,
            quote_rows=quote_rows,
        )
        report["store_path"] = str(self.path)
        report["funding_meta"] = self._latest_snapshot_meta("funding_snapshots")
        report["basis_meta"] = self._latest_snapshot_meta("basis_snapshots")
        report["quote_meta"] = self._latest_snapshot_meta("quote_snapshots")
        report["has_any_data"] = bool(funding_rows or basis_rows or quote_rows)
        return report
