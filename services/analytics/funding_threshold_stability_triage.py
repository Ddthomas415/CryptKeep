from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ARTIFACT_TYPE = "funding_threshold_stability_triage_v1"
SOURCE_ARTIFACT_TYPE = "funding_threshold_window_stability_v1"
LIMITATIONS = [
    "research_only",
    "triage_only",
    "window_stability_candidates_only",
    "not_strategy_config",
    "not_campaign_evidence",
    "not_promotion_evidence",
    "not_profitability_evidence",
    "not_activation_decision",
]


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _finite_float(value: Any, *, name: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValueError(f"invalid_numeric:{name}") from exc
    if not math.isfinite(out):
        raise ValueError(f"invalid_numeric:{name}")
    return out


def _finite_float_or_none(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    if not math.isfinite(out):
        return None
    return out


def _ratio(value: Any, *, name: str) -> float:
    out = _finite_float(value, name=name)
    if out < 0.0 or out > 1.0:
        raise ValueError(f"invalid_ratio:{name}")
    return out


def _load_source(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("input_unreadable") from exc
    if not isinstance(payload, dict):
        raise ValueError("input_not_object")
    if payload.get("artifact_type") != SOURCE_ARTIFACT_TYPE:
        raise ValueError("unsupported_input_artifact_type")
    rows = payload.get("threshold_stability")
    if not isinstance(rows, list):
        raise ValueError("input_threshold_stability_missing")
    return payload


def _thresholds(
    *,
    min_window_count: int,
    min_actionable_window_ratio: float,
    min_positive_actionable_window_ratio: float,
    min_avg_net_forward_return_pct: float,
    min_worst_window_avg_net_forward_return_pct: float,
) -> dict[str, Any]:
    return {
        "min_window_count": max(1, int(min_window_count)),
        "min_actionable_window_ratio": _ratio(min_actionable_window_ratio, name="min_actionable_window_ratio"),
        "min_positive_actionable_window_ratio": _ratio(
            min_positive_actionable_window_ratio,
            name="min_positive_actionable_window_ratio",
        ),
        "min_avg_net_forward_return_pct_across_actionable_windows": _finite_float(
            min_avg_net_forward_return_pct,
            name="min_avg_net_forward_return_pct",
        ),
        "min_worst_window_avg_net_forward_return_pct": _finite_float(
            min_worst_window_avg_net_forward_return_pct,
            name="min_worst_window_avg_net_forward_return_pct",
        ),
    }


def _thresholds_or_error(
    *,
    min_window_count: int,
    min_actionable_window_ratio: float,
    min_positive_actionable_window_ratio: float,
    min_avg_net_forward_return_pct: float,
    min_worst_window_avg_net_forward_return_pct: float,
) -> tuple[dict[str, Any], str | None]:
    try:
        return (
            _thresholds(
                min_window_count=min_window_count,
                min_actionable_window_ratio=min_actionable_window_ratio,
                min_positive_actionable_window_ratio=min_positive_actionable_window_ratio,
                min_avg_net_forward_return_pct=min_avg_net_forward_return_pct,
                min_worst_window_avg_net_forward_return_pct=min_worst_window_avg_net_forward_return_pct,
            ),
            None,
        )
    except ValueError as exc:
        return ({}, str(exc))


def _evaluate_row(row: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    window_count = int(row.get("window_count") or 0)
    actionable_window_ratio = _finite_float_or_none(row.get("actionable_window_ratio"))
    positive_window_ratio = _finite_float_or_none(row.get("positive_actionable_window_ratio"))
    avg_return = _finite_float_or_none(row.get("avg_net_forward_return_pct_across_actionable_windows"))
    worst_return = _finite_float_or_none(row.get("worst_window_avg_net_forward_return_pct"))
    reasons: list[str] = []

    if window_count < int(thresholds["min_window_count"]):
        reasons.append("insufficient_windows")
    if actionable_window_ratio is None:
        reasons.append("missing_actionable_window_ratio")
    elif actionable_window_ratio < float(thresholds["min_actionable_window_ratio"]):
        reasons.append("actionable_window_ratio_below_threshold")
    if positive_window_ratio is None:
        reasons.append("missing_positive_actionable_window_ratio")
    elif positive_window_ratio < float(thresholds["min_positive_actionable_window_ratio"]):
        reasons.append("positive_window_ratio_below_threshold")
    if avg_return is None:
        reasons.append("missing_avg_net_forward_return")
    elif avg_return < float(thresholds["min_avg_net_forward_return_pct_across_actionable_windows"]):
        reasons.append("avg_net_forward_return_below_threshold")
    if worst_return is None:
        reasons.append("missing_worst_window_return")
    elif worst_return < float(thresholds["min_worst_window_avg_net_forward_return_pct"]):
        reasons.append("worst_window_return_below_threshold")

    return {
        "long_threshold_pct": _finite_float(row.get("long_threshold_pct"), name="long_threshold_pct"),
        "short_threshold_pct": _finite_float(row.get("short_threshold_pct"), name="short_threshold_pct"),
        "status": "candidate_for_manual_review" if not reasons else "not_candidate",
        "reasons": reasons,
        "window_count": window_count,
        "actionable_window_ratio": actionable_window_ratio,
        "positive_actionable_window_ratio": positive_window_ratio,
        "avg_net_forward_return_pct_across_actionable_windows": avg_return,
        "worst_window_avg_net_forward_return_pct": worst_return,
        "false_positive_proxy": {
            "metric": "non_positive_actionable_window_ratio",
            "value": round(1.0 - positive_window_ratio, 8) if positive_window_ratio is not None else None,
            "interpretation": "share of actionable windows whose average modeled forward return was not positive",
        },
    }


def _rank_key(candidate: dict[str, Any]) -> tuple[int, float, float, float, float, float]:
    status_rank = 0 if candidate.get("status") == "candidate_for_manual_review" else 1
    avg_return = _finite_float_or_none(candidate.get("avg_net_forward_return_pct_across_actionable_windows"))
    positive_ratio = _finite_float_or_none(candidate.get("positive_actionable_window_ratio"))
    worst_return = _finite_float_or_none(candidate.get("worst_window_avg_net_forward_return_pct"))
    return (
        status_rank,
        -(avg_return if avg_return is not None else -9999.0),
        -(positive_ratio if positive_ratio is not None else -1.0),
        -(worst_return if worst_return is not None else -9999.0),
        float(candidate.get("long_threshold_pct") or 0.0),
        float(candidate.get("short_threshold_pct") or 0.0),
    )


def build_funding_threshold_stability_triage(
    *,
    stability_report: dict[str, Any],
    min_window_count: int = 2,
    min_actionable_window_ratio: float = 0.50,
    min_positive_actionable_window_ratio: float = 0.50,
    min_avg_net_forward_return_pct: float = 0.0,
    min_worst_window_avg_net_forward_return_pct: float = 0.0,
) -> dict[str, Any]:
    thresholds, threshold_error = _thresholds_or_error(
        min_window_count=min_window_count,
        min_actionable_window_ratio=min_actionable_window_ratio,
        min_positive_actionable_window_ratio=min_positive_actionable_window_ratio,
        min_avg_net_forward_return_pct=min_avg_net_forward_return_pct,
        min_worst_window_avg_net_forward_return_pct=min_worst_window_avg_net_forward_return_pct,
    )
    if threshold_error is not None or not bool(stability_report.get("ok")):
        return {
            "ok": False,
            "reason": threshold_error or str(stability_report.get("reason") or "stability_report_not_ok"),
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "source_artifact_type": stability_report.get("artifact_type"),
            "source_dataset_hash": stability_report.get("dataset_hash"),
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }

    candidates = [
        _evaluate_row(dict(row or {}), thresholds)
        for row in list(stability_report.get("threshold_stability") or [])
    ]
    candidates.sort(key=_rank_key)
    review_candidates = [
        row for row in candidates if row.get("status") == "candidate_for_manual_review"
    ]
    payload_for_hash = {
        "artifact_type": ARTIFACT_TYPE,
        "source_dataset_hash": stability_report.get("dataset_hash"),
        "thresholds": thresholds,
        "candidates": candidates,
    }
    return {
        "ok": True,
        "reason": "ok",
        "artifact_type": ARTIFACT_TYPE,
        "research_only": True,
        "source_artifact_type": stability_report.get("artifact_type"),
        "source_dataset_hash": stability_report.get("dataset_hash"),
        "dataset_hash": _sha(payload_for_hash),
        "fee_bps": stability_report.get("fee_bps"),
        "slippage_bps": stability_report.get("slippage_bps"),
        "input_rows": stability_report.get("input_rows"),
        "window_count": stability_report.get("window_count"),
        "thresholds": thresholds,
        "evaluated_threshold_pair_count": len(candidates),
        "candidate_count": len(review_candidates),
        "candidates": candidates,
        "review_candidates": review_candidates,
        "review_required_before_use": True,
        "limitations": LIMITATIONS,
    }


def run_funding_threshold_stability_triage(
    *,
    input_path: str | Path,
    min_window_count: int = 2,
    min_actionable_window_ratio: float = 0.50,
    min_positive_actionable_window_ratio: float = 0.50,
    min_avg_net_forward_return_pct: float = 0.0,
    min_worst_window_avg_net_forward_return_pct: float = 0.0,
) -> dict[str, Any]:
    try:
        source = _load_source(input_path)
        return build_funding_threshold_stability_triage(
            stability_report=source,
            min_window_count=min_window_count,
            min_actionable_window_ratio=min_actionable_window_ratio,
            min_positive_actionable_window_ratio=min_positive_actionable_window_ratio,
            min_avg_net_forward_return_pct=min_avg_net_forward_return_pct,
            min_worst_window_avg_net_forward_return_pct=min_worst_window_avg_net_forward_return_pct,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "thresholds": {},
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }
