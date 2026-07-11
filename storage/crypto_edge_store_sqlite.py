from __future__ import annotations

import json
import math
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

CREATE TABLE IF NOT EXISTS open_interest_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id TEXT NOT NULL,
  capture_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  open_interest REAL NOT NULL,
  price_change_pct REAL,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_open_interest_snapshots_capture_ts
  ON open_interest_snapshots(capture_ts DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_open_interest_snapshots_snapshot_id
  ON open_interest_snapshots(snapshot_id, id);

CREATE TABLE IF NOT EXISTS order_book_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id TEXT NOT NULL,
  capture_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  depth INTEGER NOT NULL,
  best_bid REAL NOT NULL,
  best_ask REAL NOT NULL,
  spread_bps REAL NOT NULL,
  bid_notional REAL NOT NULL,
  ask_notional REAL NOT NULL,
  imbalance REAL NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_book_snapshots_capture_ts
  ON order_book_snapshots(capture_ts DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_order_book_snapshots_snapshot_id
  ON order_book_snapshots(snapshot_id, id);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _required_float(row: dict[str, Any], key: str) -> float:
    try:
        parsed = float(row.get(key))
    except Exception as exc:
        raise ValueError(f"invalid_numeric:{key}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"invalid_numeric:{key}")
    return parsed


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

    def append_open_interest_rows(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        source: str = "manual",
        capture_ts: str | None = None,
        snapshot_id: str | None = None,
    ) -> str:
        snap_id = str(snapshot_id or _snapshot_id("open-interest"))
        ts = str(capture_ts or _now_iso())
        items = [dict(row or {}) for row in list(rows or [])]
        with self._connect() as conn:
            for row in items:
                payload = {
                    "symbol": _s(row.get("symbol")),
                    "venue": _s(row.get("venue")),
                    "open_interest": _required_float(row, "open_interest"),
                    "price_change_pct": row.get("price_change_pct"),
                }
                if payload["open_interest"] < 0.0:
                    raise ValueError("invalid_numeric:open_interest")
                conn.execute(
                    """
                    INSERT INTO open_interest_snapshots(
                      snapshot_id, capture_ts, source, symbol, venue, open_interest, price_change_pct, payload_json
                    ) VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        snap_id,
                        ts,
                        str(source or "manual"),
                        payload["symbol"],
                        payload["venue"],
                        payload["open_interest"],
                        payload["price_change_pct"],
                        json.dumps(payload, default=str),
                    ),
                )
            conn.commit()
        return snap_id

    def append_order_book_rows(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        source: str = "manual",
        capture_ts: str | None = None,
        snapshot_id: str | None = None,
    ) -> str:
        snap_id = str(snapshot_id or _snapshot_id("order-book"))
        ts = str(capture_ts or _now_iso())
        items = [dict(row or {}) for row in list(rows or [])]
        with self._connect() as conn:
            for row in items:
                payload = {
                    "symbol": _s(row.get("symbol")),
                    "venue": _s(row.get("venue")),
                    "depth": int(_required_float(row, "depth")),
                    "best_bid": _required_float(row, "best_bid"),
                    "best_ask": _required_float(row, "best_ask"),
                    "spread_bps": _required_float(row, "spread_bps"),
                    "bid_notional": _required_float(row, "bid_notional"),
                    "ask_notional": _required_float(row, "ask_notional"),
                    "imbalance": _required_float(row, "imbalance"),
                }
                if payload["depth"] <= 0:
                    raise ValueError("invalid_numeric:depth")
                if payload["best_bid"] <= 0.0 or payload["best_ask"] <= 0.0:
                    raise ValueError("invalid_numeric:best_bid_ask")
                if payload["bid_notional"] < 0.0 or payload["ask_notional"] < 0.0:
                    raise ValueError("invalid_numeric:depth_notional")
                if payload["imbalance"] < -1.0 or payload["imbalance"] > 1.0:
                    raise ValueError("invalid_numeric:imbalance")
                conn.execute(
                    """
                    INSERT INTO order_book_snapshots(
                      snapshot_id, capture_ts, source, symbol, venue, depth,
                      best_bid, best_ask, spread_bps, bid_notional, ask_notional, imbalance, payload_json
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        snap_id,
                        ts,
                        str(source or "manual"),
                        payload["symbol"],
                        payload["venue"],
                        payload["depth"],
                        payload["best_bid"],
                        payload["best_ask"],
                        payload["spread_bps"],
                        payload["bid_notional"],
                        payload["ask_notional"],
                        payload["imbalance"],
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

    def _latest_snapshot_rows_for_source(self, table: str, *, source: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT snapshot_id, capture_ts, source FROM {table} "
                "WHERE source = ? ORDER BY capture_ts DESC, id DESC LIMIT 1",
                (str(source or ""),),
            ).fetchone()
            if not row:
                return []
            rows = conn.execute(
                f"SELECT payload_json FROM {table} WHERE snapshot_id = ? ORDER BY id ASC",
                (str(row["snapshot_id"]),),
            ).fetchall()
        return [dict(json.loads(str(item["payload_json"]))) for item in rows]

    def _snapshot_rows(self, table: str, snapshot_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT payload_json FROM {table} WHERE snapshot_id = ? ORDER BY id ASC",
                (str(snapshot_id),),
            ).fetchall()
        return [dict(json.loads(str(item["payload_json"]))) for item in rows]

    def latest_funding_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("funding_snapshots")

    def latest_basis_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("basis_snapshots")

    def latest_quote_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("quote_snapshots")

    def latest_open_interest_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("open_interest_snapshots")

    def latest_order_book_rows(self) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows("order_book_snapshots")

    def latest_funding_rows_for_source(self, *, source: str) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows_for_source("funding_snapshots", source=source)

    def recent_funding_rows_for_source(self, *, source: str, limit: int = 500) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT snapshot_id, capture_ts, source, symbol, venue, funding_rate, interval_hours, payload_json
                FROM funding_snapshots
                WHERE source = ?
                ORDER BY capture_ts DESC, id DESC
                LIMIT ?
                """,
                (str(source or ""), int(max(limit, 1))),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(json.loads(str(row["payload_json"] or "{}")))
            payload.update(
                {
                    "snapshot_id": str(row["snapshot_id"]),
                    "capture_ts": str(row["capture_ts"]),
                    "source": str(row["source"]),
                    "symbol": str(row["symbol"]),
                    "venue": str(row["venue"]),
                    "funding_rate": float(row["funding_rate"]),
                    "interval_hours": float(row["interval_hours"]),
                }
            )
            out.append(payload)
        return out

    def latest_basis_rows_for_source(self, *, source: str) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows_for_source("basis_snapshots", source=source)

    def latest_quote_rows_for_source(self, *, source: str) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows_for_source("quote_snapshots", source=source)

    def latest_open_interest_rows_for_source(self, *, source: str) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows_for_source("open_interest_snapshots", source=source)

    def latest_order_book_rows_for_source(self, *, source: str) -> list[dict[str, Any]]:
        return self._latest_snapshot_rows_for_source("order_book_snapshots", source=source)

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

    def _latest_snapshot_meta_for_source(self, table: str, *, source: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT snapshot_id, capture_ts, source, COUNT(*) AS row_count FROM {table} "
                "WHERE source = ? "
                "GROUP BY snapshot_id, capture_ts, source "
                "ORDER BY capture_ts DESC LIMIT 1",
                (str(source or ""),),
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
            + self._recent_snapshot_meta("open_interest_snapshots", kind="open_interest", limit=limit_per_kind)
            + self._recent_snapshot_meta("order_book_snapshots", kind="order_books", limit=limit_per_kind)
        )
        rows.sort(key=lambda row: str(row.get("capture_ts") or ""), reverse=True)
        return rows

    def recent_funding_history(self, *, limit: int = 5) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for meta in self._recent_snapshot_meta("funding_snapshots", kind="funding", limit=limit):
            summary = build_crypto_edge_report(
                funding_rows=self._snapshot_rows("funding_snapshots", str(meta["snapshot_id"])),
            )["funding"]
            out.append(
                {
                    "capture_ts": str(meta["capture_ts"]),
                    "source": str(meta["source"]),
                    "snapshot_id": str(meta["snapshot_id"]),
                    "row_count": int(meta["row_count"] or 0),
                    "annualized_carry_pct": float(summary.get("annualized_carry_pct") or 0.0),
                    "dominant_bias": str(summary.get("dominant_bias") or "flat"),
                    "positive_ratio": float(summary.get("positive_ratio") or 0.0),
                }
            )
        return out

    def recent_basis_history(self, *, limit: int = 5) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for meta in self._recent_snapshot_meta("basis_snapshots", kind="basis", limit=limit):
            summary = build_crypto_edge_report(
                basis_rows=self._snapshot_rows("basis_snapshots", str(meta["snapshot_id"])),
            )["basis"]
            out.append(
                {
                    "capture_ts": str(meta["capture_ts"]),
                    "source": str(meta["source"]),
                    "snapshot_id": str(meta["snapshot_id"]),
                    "row_count": int(meta["row_count"] or 0),
                    "avg_basis_bps": float(summary.get("avg_basis_bps") or 0.0),
                    "widest_basis_bps": float(summary.get("widest_basis_bps") or 0.0),
                    "premium_ratio": float(summary.get("premium_ratio") or 0.0),
                }
            )
        return out

    def recent_dislocation_history(self, *, limit: int = 5) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for meta in self._recent_snapshot_meta("quote_snapshots", kind="quotes", limit=limit):
            summary = build_crypto_edge_report(
                quote_rows=self._snapshot_rows("quote_snapshots", str(meta["snapshot_id"])),
            )["dislocations"]
            top = dict(summary.get("top_dislocation") or {})
            out.append(
                {
                    "capture_ts": str(meta["capture_ts"]),
                    "source": str(meta["source"]),
                    "snapshot_id": str(meta["snapshot_id"]),
                    "row_count": int(meta["row_count"] or 0),
                    "positive_count": int(summary.get("positive_count") or 0),
                    "top_symbol": str(top.get("symbol") or "-"),
                    "top_gross_cross_bps": float(top.get("gross_cross_bps") or 0.0),
                }
            )
        return out

    def latest_report(self) -> dict[str, Any]:
        funding_rows = self.latest_funding_rows()
        basis_rows = self.latest_basis_rows()
        quote_rows = self.latest_quote_rows()
        open_interest_rows = self.latest_open_interest_rows()
        order_book_rows = self.latest_order_book_rows()
        report = build_crypto_edge_report(
            funding_rows=funding_rows,
            basis_rows=basis_rows,
            quote_rows=quote_rows,
            open_interest_rows=open_interest_rows,
            order_book_rows=order_book_rows,
        )
        report["store_path"] = "redacted"
        report["funding_meta"] = self._latest_snapshot_meta("funding_snapshots")
        report["basis_meta"] = self._latest_snapshot_meta("basis_snapshots")
        report["quote_meta"] = self._latest_snapshot_meta("quote_snapshots")
        report["open_interest_meta"] = self._latest_snapshot_meta("open_interest_snapshots")
        report["order_book_meta"] = self._latest_snapshot_meta("order_book_snapshots")
        report["has_any_data"] = bool(funding_rows or basis_rows or quote_rows or open_interest_rows or order_book_rows)
        return report

    def latest_report_for_source(self, *, source: str) -> dict[str, Any]:
        funding_rows = self.latest_funding_rows_for_source(source=source)
        basis_rows = self.latest_basis_rows_for_source(source=source)
        quote_rows = self.latest_quote_rows_for_source(source=source)
        open_interest_rows = self.latest_open_interest_rows_for_source(source=source)
        order_book_rows = self.latest_order_book_rows_for_source(source=source)
        report = build_crypto_edge_report(
            funding_rows=funding_rows,
            basis_rows=basis_rows,
            quote_rows=quote_rows,
            open_interest_rows=open_interest_rows,
            order_book_rows=order_book_rows,
        )
        report["store_path"] = "redacted"
        report["funding_meta"] = self._latest_snapshot_meta_for_source("funding_snapshots", source=source)
        report["basis_meta"] = self._latest_snapshot_meta_for_source("basis_snapshots", source=source)
        report["quote_meta"] = self._latest_snapshot_meta_for_source("quote_snapshots", source=source)
        report["open_interest_meta"] = self._latest_snapshot_meta_for_source("open_interest_snapshots", source=source)
        report["order_book_meta"] = self._latest_snapshot_meta_for_source("order_book_snapshots", source=source)
        report["has_any_data"] = bool(funding_rows or basis_rows or quote_rows or open_interest_rows or order_book_rows)
        report["source_filter"] = str(source or "")
        return report
