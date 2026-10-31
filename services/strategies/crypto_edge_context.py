from __future__ import annotations

import math
import os
import json
import sqlite3
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.market_data.symbol_router import normalize_symbol, normalize_venue
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite, DB_PATH as DEFAULT_EDGE_STORE_DB_PATH


EDGE_STORE_DB_PATH_ENV = "CBP_CRYPTO_EDGE_DB_PATH"
DEFAULT_CONTEXT_SOURCE = "live_public"
DEFAULT_FUNDING_MAX_AGE_SEC = 36 * 60 * 60


def _parse_ts(value: Any) -> datetime | None:
    try:
        raw = str(value or "").strip()
        if not raw:
            return None
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _finite_float(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    if not math.isfinite(out):
        return None
    return out


def _same_symbol(left: Any, right: Any) -> bool:
    return normalize_symbol(str(left or "")) == normalize_symbol(str(right or ""))


def _same_venue(left: Any, right: Any) -> bool:
    return normalize_venue(str(left or "")) == normalize_venue(str(right or ""))


def _read_legacy_rows(path: Path, source: str) -> list[dict[str, Any]]:
    # No store constructor: initialization would execute DDL on a read path.
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute(
            "SELECT snapshot_id,capture_ts,source,symbol,venue,funding_rate,interval_hours,payload_json "
            "FROM funding_snapshots WHERE source=? ORDER BY capture_ts DESC,id DESC LIMIT 500",
            (source,),
        ).fetchall()
    finally:
        conn.close()
    result = []
    for row in rows:
        payload = dict(json.loads(row["payload_json"]))
        payload.update({key: row[key] for key in (
            "snapshot_id", "capture_ts", "source", "symbol", "venue", "funding_rate", "interval_hours")})
        result.append(payload)
    return result


def funding_context_from_crypto_edge_store(
    *,
    symbol: str,
    venue: str,
    source: str = DEFAULT_CONTEXT_SOURCE,
    max_age_sec: float = DEFAULT_FUNDING_MAX_AGE_SEC,
    store_path: str | Path | None = None,
    store: CryptoEdgeStoreSQLite | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Inspect stored legacy funding without qualifying it for funding_extreme.

    Default path uses SQLite mode=ro, not a schema-initializing constructor.
    Caller-supplied stores own their read behavior. Legacy source/interval
    provenance is insufficient even when rows are fresh and well-formed.
    """
    clean_source = str(source or DEFAULT_CONTEXT_SOURCE).strip() or DEFAULT_CONTEXT_SOURCE
    clean_symbol = normalize_symbol(str(symbol or ""))
    clean_venue = normalize_venue(str(venue or ""))
    if not clean_symbol or not clean_venue:
        return {
            "ok": False,
            "reason": "funding_context_missing_contract",
            "source": clean_source,
            "symbol": clean_symbol,
            "venue": clean_venue,
        }

    edge_store_path = str(store_path or os.environ.get(EDGE_STORE_DB_PATH_ENV) or DEFAULT_EDGE_STORE_DB_PATH).strip()
    if store is None:
        resolved = Path(edge_store_path).expanduser().resolve()
        if not resolved.exists():
            return {
                "ok": False,
                "reason": "funding_context_store_missing",
                "source": clean_source,
                "symbol": clean_symbol,
                "venue": clean_venue,
                "store_path": str(resolved),
            }
    try:
        rows = (store.recent_funding_rows_for_source(source=clean_source, limit=500)
                if store is not None else _read_legacy_rows(resolved, clean_source))
    except Exception as exc:
        return {
            "ok": False,
            "reason": "funding_context_store_error",
            "error_type": type(exc).__name__,
            "source": clean_source,
            "symbol": clean_symbol,
            "venue": clean_venue,
        }

    selected: dict[str, Any] | None = None
    for row in rows:
        if _same_symbol(row.get("symbol"), clean_symbol) and _same_venue(row.get("venue"), clean_venue):
            selected = dict(row)
            break
    if not selected:
        return {
            "ok": False,
            "reason": "funding_context_missing",
            "source": clean_source,
            "symbol": clean_symbol,
            "venue": clean_venue,
        }

    rate = _finite_float(selected.get("funding_rate"))
    if rate is None:
        return {
            "ok": False,
            "reason": "funding_context_invalid_rate",
            "source": clean_source,
            "symbol": clean_symbol,
            "venue": clean_venue,
            "capture_ts": selected.get("capture_ts"),
            "snapshot_id": selected.get("snapshot_id"),
        }

    capture_ts = _parse_ts(selected.get("capture_ts"))
    if capture_ts is None:
        return {
            "ok": False,
            "reason": "funding_context_invalid_capture_ts",
            "source": clean_source,
            "symbol": clean_symbol,
            "venue": clean_venue,
            "capture_ts": selected.get("capture_ts"),
            "snapshot_id": selected.get("snapshot_id"),
        }

    now_ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    try:
        max_age = float(max_age_sec)
    except Exception:
        max_age = DEFAULT_FUNDING_MAX_AGE_SEC
    if not math.isfinite(max_age):
        max_age = DEFAULT_FUNDING_MAX_AGE_SEC
    age_sec = max(0.0, (now_ts - capture_ts).total_seconds())
    if max_age > 0.0 and age_sec > max_age:
        return {
            "ok": False,
            "reason": "funding_context_stale",
            "source": clean_source,
            "symbol": clean_symbol,
            "venue": clean_venue,
            "capture_ts": capture_ts.isoformat(),
            "age_sec": age_sec,
            "max_age_sec": max_age,
            "snapshot_id": selected.get("snapshot_id"),
        }

    return {
        "ok": False,
        "reason": "funding_context_unqualified",
        "source": clean_source,
        "symbol": clean_symbol,
        "venue": clean_venue,
        "capture_ts": capture_ts.isoformat(),
        "age_sec": age_sec,
        "snapshot_id": selected.get("snapshot_id"),
        "normalization_eligible": False,
        "raw_observation": deepcopy(selected),
        "qualification_required": ["native_rate_semantics", "effective_interval",
                                   "cash_cost_basis", "crowding_comparability"],
    }
