from __future__ import annotations

import math
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Slow-cadence history families are enabled by default. The 12h default checks
# collector freshness without assuming each venue updates funding every hour.
DEFAULT_MAX_AGE_SEC: dict[str, float] = {
    "funding": 12 * 3600.0,
    "open_interest": 12 * 3600.0,
    "basis": 12 * 3600.0,
    "quote": 0.0,
    "order_book": 0.0,
}

META_KEYS = {
    "funding": "funding_meta",
    "open_interest": "open_interest_meta",
    "basis": "basis_meta",
    "quote": "quote_meta",
    "order_book": "order_book_meta",
}

TABLES = {
    "funding": "funding_snapshots",
    "open_interest": "open_interest_snapshots",
    "basis": "basis_snapshots",
    "quote": "quote_snapshots",
    "order_book": "order_book_snapshots",
}


@dataclass(frozen=True)
class FamilyCadence:
    family: str
    max_age_sec: float
    capture_ts: str | None
    age_sec: float | None
    status: str
    reason: str


def _env_age_sec(family: str, default: float) -> float:
    raw = str(os.environ.get(f"CBP_EDGE_MAX_AGE_{family.upper()}_SEC") or "").strip()
    if not raw:
        return float(default)
    try:
        value = float(raw)
    except Exception:
        return float(default)
    if not math.isfinite(value) or value < 0.0:
        return float(default)
    return value


def _parse_ts(raw: Any) -> datetime | None:
    try:
        text = str(raw or "").strip()
        if not text:
            return None
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def evaluate_cadence(
    report: dict[str, Any],
    *,
    now: datetime | None = None,
    max_age_sec: dict[str, float] | None = None,
) -> dict[str, Any]:
    ref = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    thresholds = dict(DEFAULT_MAX_AGE_SEC)
    if max_age_sec:
        thresholds.update(max_age_sec)

    families: list[FamilyCadence] = []
    for family, meta_key in META_KEYS.items():
        limit = _env_age_sec(family, thresholds.get(family, 0.0))
        if limit <= 0.0:
            families.append(FamilyCadence(family, limit, None, None, "disabled", "check_disabled"))
            continue

        meta = report.get(meta_key) if isinstance(report, dict) else None
        if not isinstance(meta, dict) or not meta.get("capture_ts"):
            families.append(FamilyCadence(family, limit, None, None, "missing", "no_snapshot"))
            continue

        capture = _parse_ts(meta.get("capture_ts"))
        if capture is None:
            families.append(
                FamilyCadence(family, limit, str(meta.get("capture_ts")), None, "missing", "unparseable_capture_ts")
            )
            continue

        age = max(0.0, (ref - capture).total_seconds())
        if age > limit:
            families.append(
                FamilyCadence(family, limit, capture.isoformat(), age, "stale", f"age_sec={age:.0f} max={limit:.0f}")
            )
        else:
            families.append(FamilyCadence(family, limit, capture.isoformat(), age, "ok", "fresh"))

    enabled = [f for f in families if f.status != "disabled"]
    stale = [f.family for f in enabled if f.status == "stale"]
    missing = [f.family for f in enabled if f.status == "missing"]
    return {
        "ok": bool(enabled) and not stale and not missing,
        "checked": [f.family for f in enabled],
        "stale": stale,
        "missing": missing,
        "families": [f.__dict__ for f in families],
    }


def _default_store_path() -> Path:
    from storage.crypto_edge_store_sqlite import DB_PATH

    return Path(DB_PATH)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _latest_snapshot_meta_read_only(conn: sqlite3.Connection, table: str) -> dict[str, Any] | None:
    if not _table_exists(conn, table):
        return None
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


def _latest_report_read_only(store_path: str | None = None) -> dict[str, Any]:
    path = Path(store_path).expanduser() if store_path else _default_store_path()
    if not path.exists():
        return {"store_path": str(path), "has_any_data": False}
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        report: dict[str, Any] = {"store_path": "redacted"}
        for family, meta_key in META_KEYS.items():
            report[meta_key] = _latest_snapshot_meta_read_only(conn, TABLES[family])
        report["has_any_data"] = any(bool(report.get(meta_key)) for meta_key in META_KEYS.values())
        return report
    finally:
        conn.close()


def check_edge_cadence(
    *,
    store_path: str | None = None,
    now: datetime | None = None,
    max_age_sec: dict[str, float] | None = None,
) -> dict[str, Any]:
    try:
        report = _latest_report_read_only(store_path=store_path)
    except Exception as exc:
        return {
            "ok": False,
            "checked": [],
            "stale": [],
            "missing": list(META_KEYS.keys()),
            "families": [],
            "store_error": f"{type(exc).__name__}: {exc}",
        }
    return evaluate_cadence(report, now=now, max_age_sec=max_age_sec)
