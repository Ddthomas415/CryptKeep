from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from services.control.paper_promotion_progress import load_paper_promotion_progress


def _parse_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _round2(value: float | None) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return round(float(value), 2)


def _qualified_close_times(qualification: dict[str, Any]) -> list[datetime]:
    values = qualification.get("completed_round_trip_close_timestamps")
    if not isinstance(values, list):
        values = []
    parsed = [_parse_ts(value) for value in values]
    return sorted({item for item in parsed if item is not None})


def compute_round_trip_velocity(
    *,
    close_timestamps: list[Any],
    recorded: int,
    required: int,
    reference_ts: datetime | None = None,
) -> dict[str, Any]:
    """Estimate gate completion from observed qualified close cadence.

    This is diagnostic only. It never changes promotion policy or evidence
    qualification; with fewer than two qualified closes it refuses to project.
    """

    now = reference_ts or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    remaining = max(0, int(required) - int(recorded))
    times = sorted(
        {
            parsed
            for value in list(close_timestamps or [])
            if (parsed := _parse_ts(value)) is not None
        }
    )
    if remaining <= 0:
        return {
            "status": "complete",
            "can_estimate": True,
            "qualified_round_trips_recorded": int(recorded),
            "qualified_round_trips_required": int(required),
            "qualified_round_trips_remaining": 0,
            "qualified_close_count": len(times),
            "observed_span_days": 0.0,
            "mean_days_per_qualified_round_trip": 0.0,
            "estimated_days_remaining": 0,
            "estimated_completion_ts": now.isoformat(),
            "reason": "threshold_met",
        }
    if len(times) < 2:
        return {
            "status": "insufficient_velocity_history",
            "can_estimate": False,
            "qualified_round_trips_recorded": int(recorded),
            "qualified_round_trips_required": int(required),
            "qualified_round_trips_remaining": remaining,
            "qualified_close_count": len(times),
            "observed_span_days": None,
            "mean_days_per_qualified_round_trip": None,
            "estimated_days_remaining": None,
            "estimated_completion_ts": None,
            "reason": "need_at_least_two_qualified_round_trip_closes",
        }

    span_days = max(0.0, (times[-1] - times[0]).total_seconds() / 86400.0)
    intervals = max(1, len(times) - 1)
    mean_days = span_days / float(intervals)
    if mean_days <= 0.0 or not math.isfinite(mean_days):
        return {
            "status": "insufficient_velocity_history",
            "can_estimate": False,
            "qualified_round_trips_recorded": int(recorded),
            "qualified_round_trips_required": int(required),
            "qualified_round_trips_remaining": remaining,
            "qualified_close_count": len(times),
            "observed_span_days": _round2(span_days),
            "mean_days_per_qualified_round_trip": None,
            "estimated_days_remaining": None,
            "estimated_completion_ts": None,
            "reason": "non_positive_observed_cadence",
        }

    days_remaining = int(math.ceil(float(remaining) * mean_days))
    completion = now + timedelta(days=days_remaining)
    return {
        "status": "projected",
        "can_estimate": True,
        "qualified_round_trips_recorded": int(recorded),
        "qualified_round_trips_required": int(required),
        "qualified_round_trips_remaining": remaining,
        "qualified_close_count": len(times),
        "first_qualified_close_ts": times[0].isoformat(),
        "latest_qualified_close_ts": times[-1].isoformat(),
        "observed_span_days": _round2(span_days),
        "mean_days_per_qualified_round_trip": _round2(mean_days),
        "estimated_days_remaining": days_remaining,
        "estimated_completion_ts": completion.isoformat(),
        "reason": "projection_uses_mean_observed_qualified_close_cadence",
    }


def build_paper_gate_velocity_report(
    *,
    reference_ts: datetime | None = None,
) -> dict[str, Any]:
    progress = load_paper_promotion_progress()
    qualification = dict(progress.get("qualification") or {})
    close_times = _qualified_close_times(qualification)
    velocity = compute_round_trip_velocity(
        close_timestamps=[item.isoformat() for item in close_times],
        recorded=int(progress.get("round_trips_recorded") or 0),
        required=int(progress.get("round_trips_required") or 0),
        reference_ts=reference_ts,
    )
    all_history = int(progress.get("all_history_round_trips") or 0)
    qualified = int(progress.get("round_trips_recorded") or 0)
    excluded = max(0, all_history - qualified)
    findings: list[dict[str, Any]] = []
    if excluded:
        findings.append(
            {
                "id": "legacy_history_excluded",
                "severity": "info",
                "summary": (
                    f"{excluded} all-history round trip(s) are diagnostic only "
                    "because they do not satisfy the current provenance contract."
                ),
            }
        )
    if velocity["status"] == "projected" and int(velocity["estimated_days_remaining"] or 0) > 60:
        findings.append(
            {
                "id": "slow_gate_velocity",
                "severity": "warning",
                "summary": (
                    "Observed qualified round-trip cadence projects more than "
                    "60 days remaining under the current gate."
                ),
            }
        )
    if int(progress.get("qualified_bars_required") or 0) > 0 and not bool(
        progress.get("qualified_bars_ready")
    ):
        findings.append(
            {
                "id": "qualified_bars_remaining",
                "severity": "info",
                "summary": (
                    f"{int(progress.get('qualified_bars_remaining') or 0)} qualified "
                    "source bar(s) remain under the configured policy."
                ),
            }
        )

    return {
        "ok": True,
        "read_only": True,
        "report_type": "paper_gate_velocity",
        "strategy_id": progress.get("strategy_id"),
        "target_strategy": progress.get("target_strategy"),
        "policy_id": progress.get("policy_id"),
        "policy_valid": bool(progress.get("policy_valid")),
        "thresholds_ready": bool(progress.get("thresholds_ready")),
        "round_trips": {
            "qualified": qualified,
            "required": int(progress.get("round_trips_required") or 0),
            "remaining": int(progress.get("round_trips_remaining") or 0),
            "all_history": all_history,
            "excluded_all_history": excluded,
        },
        "days": {
            "recorded": int(progress.get("days_recorded") or 0),
            "required": int(progress.get("days_required") or 0),
            "remaining": int(progress.get("days_remaining") or 0),
        },
        "qualified_bars": {
            "enabled": bool(progress.get("qualified_bars_enabled")),
            "recorded": int(progress.get("qualified_bars_recorded") or 0),
            "required": int(progress.get("qualified_bars_required") or 0),
            "remaining": int(progress.get("qualified_bars_remaining") or 0),
            "ready": bool(progress.get("qualified_bars_ready")),
            "source": str(progress.get("bar_count_source") or "none"),
        },
        "velocity": velocity,
        "qualification_explanation": progress.get("qualification_explanation"),
        "blocking_thresholds": list(progress.get("blocking_thresholds") or []),
        "findings": findings,
        "summary_text": _summary_text(progress=progress, velocity=velocity, excluded=excluded),
    }


def _summary_text(
    *,
    progress: dict[str, Any],
    velocity: dict[str, Any],
    excluded: int,
) -> str:
    base = (
        f"Paper gate velocity: {int(progress.get('round_trips_recorded') or 0)}/"
        f"{int(progress.get('round_trips_required') or 0)} qualified round trips "
        f"({int(progress.get('round_trips_remaining') or 0)} remaining)."
    )
    if velocity.get("status") == "projected":
        base = (
            f"{base} Observed cadence is "
            f"{velocity.get('mean_days_per_qualified_round_trip')} days per "
            f"qualified round trip; projected completion in "
            f"{velocity.get('estimated_days_remaining')} days "
            f"({velocity.get('estimated_completion_ts')})."
        )
    elif velocity.get("status") == "complete":
        base = f"{base} Round-trip threshold is complete."
    else:
        base = f"{base} Projection unavailable: {velocity.get('reason')}."
    if excluded:
        base = f"{base} {excluded} legacy/all-history round trip(s) remain diagnostic only."
    return base
