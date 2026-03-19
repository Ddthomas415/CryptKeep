from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from dashboard.services.digest.contracts import FreshnessState, HealthState, TruthPillData


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso(dt: datetime | None = None) -> str:
    stamp = (dt or utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    return stamp.isoformat().replace("+00:00", "Z")


def parse_iso_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_seconds(value: Any, *, now: datetime | None = None) -> int | None:
    parsed = parse_iso_ts(value)
    if parsed is None:
        return None
    reference = now or utc_now()
    return max(int((reference - parsed).total_seconds()), 0)


def coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if out != out or out in {float("inf"), float("-inf")}:
        return float(default)
    return float(out)


def fmt_pct(value: Any) -> str:
    return f"{coerce_float(value, 0.0):+.2f}%"


def fmt_pct_abs(value: Any) -> str:
    return f"{coerce_float(value, 0.0):.2f}%"


def fmt_num(value: Any) -> str:
    return f"{coerce_float(value, 0.0):.2f}"


def fmt_age(seconds: int | None) -> str:
    if seconds is None:
        return "Unknown"
    if seconds < 60:
        return f"{seconds}s old"
    if seconds < 3600:
        return f"{seconds // 60}m old"
    if seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m old" if minutes else f"{hours}h old"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    return f"{days}d {hours}h old" if hours else f"{days}d old"


def freshness_state_from_age(age_seconds: int | None) -> FreshnessState:
    if age_seconds is None:
        return "missing"
    if age_seconds < 3600:
        return "fresh"
    if age_seconds < 6 * 3600:
        return "aging"
    return "stale"


def freshness_state_from_label(label: Any, *, age_seconds: int | None = None) -> FreshnessState:
    value = str(label or "").strip().lower()
    if value in {"fresh"}:
        return "fresh"
    if value in {"aging", "recent"}:
        return "aging"
    if value in {"stale"}:
        return "stale"
    if value in {"not_active", "not active"}:
        return "not_active"
    if value in {"no live data", "missing", "unknown", "unavailable", "", "no snapshots"}:
        return "missing" if age_seconds is None else freshness_state_from_age(age_seconds)
    return freshness_state_from_age(age_seconds)


def health_from_freshness(state: FreshnessState) -> HealthState:
    if state == "fresh":
        return "ok"
    if state == "aging":
        return "warn"
    if state == "stale":
        return "critical"
    return "unknown"


def normalize_health_state(value: Any, *, default: HealthState = "unknown") -> HealthState:
    state = str(value or "").strip().lower()
    if state in {"ok", "warn", "critical", "unknown"}:
        return state  # type: ignore[return-value]
    mapping = {
        "healthy": "ok",
        "degraded": "warn",
        "blocked": "critical",
        "missing": "unknown",
        "partial": "warn",
    }
    return mapping.get(state, default)  # type: ignore[return-value]


def base_section(
    *,
    as_of: str,
    caveat: str | None = None,
    source_name: str | None = None,
    source_age_seconds: int | None = None,
) -> dict[str, Any]:
    return {
        "as_of": as_of,
        "caveat": caveat,
        "source_name": source_name,
        "source_age_seconds": source_age_seconds,
    }


def pill(
    *,
    value: str,
    label: str | None = None,
    state: str,
    caveat: str | None = None,
    age_seconds: int | None = None,
) -> TruthPillData:
    return {
        "value": value,
        "label": label or value,
        "state": state,
        "caveat": caveat,
        "age_seconds": age_seconds,
    }
