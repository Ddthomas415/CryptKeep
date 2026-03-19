from __future__ import annotations

from typing import Any

from dashboard.services.digest.utils import age_seconds, fmt_age, freshness_state_from_age


def _freshness_label(seconds: int | None) -> str:
    state = freshness_state_from_age(seconds)
    mapping = {
        "fresh": "Fresh",
        "aging": "Aging",
        "stale": "Stale",
        "missing": "Unknown",
        "not_active": "Not Active",
    }
    return mapping.get(state, "Unknown")


def load_paper_strategy_evidence_runtime() -> dict[str, Any]:
    try:
        from services.analytics.paper_strategy_evidence_service import load_runtime_status
    except Exception as exc:
        return {
            "ok": False,
            "has_status": False,
            "reason": f"service_import_failed:{type(exc).__name__}",
            "summary_text": "Paper strategy evidence collector runtime is unavailable.",
        }

    payload = dict(load_runtime_status() or {})
    age_s = age_seconds(payload.get("ts") or payload.get("started_ts"))
    payload["age_seconds"] = age_s
    payload["freshness"] = _freshness_label(age_s)
    payload["age_label"] = fmt_age(age_s)
    payload["completed_summary"] = (
        f"{int(payload.get('completed_strategies') or 0)}/{int(payload.get('total_strategies') or 0)}"
        if payload.get("total_strategies") is not None
        else "0/0"
    )
    if not str(payload.get("summary_text") or "").strip():
        payload["summary_text"] = (
            f"Paper strategy evidence collector status {str(payload.get('status') or 'unknown')}, "
            f"{payload['completed_summary']} strategies complete."
        )
    return payload
