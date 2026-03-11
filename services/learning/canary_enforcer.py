# Phase 186: Canary enforcement + auto-rollback helper
from __future__ import annotations

from typing import Any, Dict

from services.learning.runtime_policy import RuntimePolicy


def evaluate_canary(
    *,
    policy: RuntimePolicy,
    baseline_metric: float,
    candidate_metric: float,
    sample_count: int,
) -> Dict[str, Any]:
    if not policy.canary_enabled:
        return {"ok": True, "action": "promote", "reason": "canary_disabled"}
    if int(sample_count) < int(policy.canary_min_samples):
        return {"ok": False, "action": "hold", "reason": "insufficient_samples", "sample_count": int(sample_count)}

    base = float(baseline_metric)
    cand = float(candidate_metric)
    delta = cand - base

    if delta >= float(policy.promote_min_metric_delta):
        return {"ok": True, "action": "promote", "reason": "candidate_better_or_equal", "delta": float(delta)}

    if abs(delta) >= float(policy.rollback_max_metric_drop):
        return {"ok": False, "action": "rollback", "reason": "candidate_regression", "delta": float(delta)}

    return {"ok": False, "action": "hold", "reason": "no_clear_win", "delta": float(delta)}
