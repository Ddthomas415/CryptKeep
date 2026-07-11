from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
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


def check_edge_cadence(
    *,
    store_path: str | None = None,
    now: datetime | None = None,
    max_age_sec: dict[str, float] | None = None,
) -> dict[str, Any]:
    try:
        from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite

        store = CryptoEdgeStoreSQLite(path=store_path or "")
        report = store.latest_report()
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
