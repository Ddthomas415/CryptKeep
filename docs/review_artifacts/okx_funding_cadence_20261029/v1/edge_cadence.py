from __future__ import annotations

import math
import os
import json
import re
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

        if capture > ref:
            families.append(FamilyCadence(family, limit, capture.isoformat(), None, "missing", "capture_in_future"))
            continue
        age = (ref - capture).total_seconds()
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


def _paired_scope(source, inst_ids, scan_limit):
    if source is None and inst_ids is None:
        return None
    if (type(source) is not str or not source or source != source.strip()
            or type(inst_ids) not in (list, tuple) or not inst_ids
            or any(type(item) is not str or re.fullmatch(r"[A-Z0-9]+-[A-Z0-9]+-SWAP", item) is None
                   for item in inst_ids)
            or len(set(inst_ids)) != len(inst_ids)
            or type(scan_limit) is not int or not 1 <= scan_limit <= 1000):
        raise ValueError("explicit_paired_source_native_ids_and_scan_limit_required")
    return source, tuple(inst_ids), scan_limit


def _paired_funding_meta(conn, scope, ref):
    from services.analytics.okx_funding_contract import _finite_json_float, _object, _reject_nonfinite
    from services.analytics.okx_funding_journal import CONTRACT, _stored_pair

    source, inst_ids, limit = scope
    details = {"lane": "validated_okx_pair_capture", "source": source,
               "scan_limit": limit, "scanned": 0, "scan_exhaustive": False,
               "normalization_eligible": False, "strategy_eligible": False,
               "execution_authority": False, "instruments": [], "diagnostics": []}
    found = {}
    if conn is not None and _table_exists(conn, "raw_funding_observations"):
        # Bound fetched text and total decoded evidence, not just the row count.
        rows = conn.execute(
            "SELECT observation_key, capture_ts, length(CAST(payload_json AS BLOB)) AS size, "
            "CASE WHEN length(CAST(payload_json AS BLOB)) <= 4194304 THEN payload_json END AS payload "
            "FROM raw_funding_observations WHERE source=? ORDER BY id DESC LIMIT ?", (source, limit + 1))
        used = 0
        for row in rows:
            if details["scanned"] >= limit:
                break
            details["scanned"] += 1
            if row["payload"] is None or row["size"] is None or used + row["size"] > 8388608:
                details["diagnostics"].append("raw_evidence_byte_budget_exceeded")
                break
            used += row["size"]
            try:
                record = json.loads(row["payload"], object_pairs_hook=_object,
                                    parse_constant=_reject_nonfinite, parse_float=_finite_json_float)
                if type(record) is not dict:
                    raise ValueError("raw_object_required")
                inst = record.get("symbol")
                if type(inst) is not str:
                    raise ValueError("raw_identity_required")
                if inst not in inst_ids or inst in found:
                    continue
                found[inst] = {"inst_id": inst, "status": "unusable_evidence", "capture_ts": None}
                payload = record.get("raw_payload")
                if type(payload) is not dict or payload.get("contract") != CONTRACT:
                    found[inst]["status"] = "not_a_successful_pair"
                    continue
                _stored_pair(record, row["observation_key"])
                capture = _parse_ts(record["captured_at"])
                if capture is None or row["capture_ts"] != capture.isoformat():
                    raise ValueError("raw_capture_index_mismatch")
                if capture > ref:
                    found[inst]["status"] = "capture_in_future"
                    continue
                found[inst].update(status="validated_capture", capture_ts=capture.isoformat(),
                                   observation_key=row["observation_key"])
            except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
                # Unattributable corruption cannot stand in for a missing instrument.
                details["diagnostics"].append("unusable_raw_evidence")
                break
            if len(found) == len(inst_ids):
                break
        else:
            details["scan_exhaustive"] = True
        rows.close()
    else:
        details["scan_exhaustive"] = True
    details["instruments"] = [found.get(inst, {"inst_id": inst, "status": "no_capture_in_scan",
                                              "capture_ts": None}) for inst in inst_ids]
    valid = [item for item in details["instruments"] if item["status"] == "validated_capture"]
    if details["diagnostics"] or len(valid) != len(inst_ids):
        return None, details
    return {"capture_ts": min(item["capture_ts"] for item in valid), "source": source,
            "row_count": len(valid), "evidence_lane": details["lane"]}, details


def _latest_report_read_only(store_path: str | None = None, *, paired_scope=None, now=None) -> dict[str, Any]:
    path = Path(store_path).expanduser() if store_path else _default_store_path()
    if not path.exists():
        report = {"store_path": str(path), "has_any_data": False}
        if paired_scope is not None:
            report["funding_meta"], report["paired_funding"] = _paired_funding_meta(None, paired_scope, now)
        return report
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        report: dict[str, Any] = {"store_path": "redacted"}
        for family, meta_key in META_KEYS.items():
            report[meta_key] = _latest_snapshot_meta_read_only(conn, TABLES[family])
        if paired_scope is not None:
            report["funding_meta"], report["paired_funding"] = _paired_funding_meta(conn, paired_scope, now)
        report["has_any_data"] = any(bool(report.get(meta_key)) for meta_key in META_KEYS.values())
        return report
    finally:
        conn.close()


def check_edge_cadence(
    *,
    store_path: str | None = None,
    now: datetime | None = None,
    max_age_sec: dict[str, float] | None = None,
    paired_funding_source: str | None = None,
    paired_funding_inst_ids: list[str] | tuple[str, ...] | None = None,
    paired_funding_scan_limit: int = 100,
) -> dict[str, Any]:
    try:
        ref = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        scope = _paired_scope(paired_funding_source, paired_funding_inst_ids, paired_funding_scan_limit)
        report = _latest_report_read_only(store_path=store_path, paired_scope=scope, now=ref)
    except Exception as exc:
        return {
            "ok": False,
            "checked": [],
            "stale": [],
            "missing": list(META_KEYS.keys()),
            "families": [],
            "store_error": type(exc).__name__,
        }
    result = evaluate_cadence(report, now=ref, max_age_sec=max_age_sec)
    if "paired_funding" in report:
        result["paired_funding"] = report["paired_funding"]
    return result
