from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ARTIFACT_TYPE = "funding_threshold_candidate_triage_v1"
SOURCE_ARTIFACT_TYPE = "funding_threshold_sensitivity_v1"
LIMITATIONS = [
    "research_only",
    "triage_only",
    "threshold_candidates_only",
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


def _finite_int(value: Any, *, name: str) -> int:
    try:
        out = int(value)
    except Exception as exc:
        raise ValueError(f"invalid_integer:{name}") from exc
    if out < 0:
        raise ValueError(f"invalid_integer:{name}")
    return out


def _bounded_ratio(value: Any, *, name: str) -> float:
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
    rows = payload.get("grid_rows")
    if not isinstance(rows, list):
        raise ValueError("input_grid_rows_missing")
    return payload


def _thresholds(
    *,
    min_input_rows: int,
    min_actionable_rows: int,
    min_actionable_share: float,
    min_positive_ratio: float,
    min_avg_net_forward_return_pct: float,
) -> dict[str, Any]:
    return {
        "min_input_rows": max(1, int(min_input_rows)),
        "min_actionable_rows": max(1, int(min_actionable_rows)),
        "min_actionable_share": _bounded_ratio(min_actionable_share, name="min_actionable_share"),
        "min_positive_actionable_ratio": _bounded_ratio(min_positive_ratio, name="min_positive_actionable_ratio"),
        "min_avg_net_forward_return_pct": _finite_float(
            min_avg_net_forward_return_pct,
            name="min_avg_net_forward_return_pct",
        ),
    }


def _thresholds_or_error(
    *,
    min_input_rows: int,
    min_actionable_rows: int,
    min_actionable_share: float,
    min_positive_ratio: float,
    min_avg_net_forward_return_pct: float,
) -> tuple[dict[str, Any], str | None]:
    try:
        return (
            _thresholds(
                min_input_rows=min_input_rows,
                min_actionable_rows=min_actionable_rows,
                min_actionable_share=min_actionable_share,
                min_positive_ratio=min_positive_ratio,
                min_avg_net_forward_return_pct=min_avg_net_forward_return_pct,
            ),
            None,
        )
    except ValueError as exc:
        return ({}, str(exc))


def _evaluate_row(row: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    total_rows = _finite_int(row.get("total_rows", 0), name="total_rows")
    actionable_rows = _finite_int(row.get("actionable_rows", 0), name="actionable_rows")
    actionable_share = _finite_float_or_none(row.get("actionable_share"))
    positive_ratio = _finite_float_or_none(row.get("positive_actionable_ratio"))
    avg_return = _finite_float_or_none(row.get("avg_net_forward_return_pct"))
    reasons: list[str] = []

    if total_rows < int(thresholds["min_input_rows"]):
        reasons.append("insufficient_input_rows")
    if actionable_rows < int(thresholds["min_actionable_rows"]):
        reasons.append("insufficient_actionable_rows")
    if actionable_share is None:
        reasons.append("missing_actionable_share")
    elif actionable_share < float(thresholds["min_actionable_share"]):
        reasons.append("actionable_share_below_threshold")
    if positive_ratio is None:
        reasons.append("missing_positive_actionable_ratio")
    elif positive_ratio < float(thresholds["min_positive_actionable_ratio"]):
        reasons.append("positive_ratio_below_threshold")
    if avg_return is None:
        reasons.append("missing_avg_net_forward_return_pct")
    elif avg_return < float(thresholds["min_avg_net_forward_return_pct"]):
        reasons.append("avg_net_forward_return_below_threshold")

    return {
        "long_threshold_pct": _finite_float(row.get("long_threshold_pct"), name="long_threshold_pct"),
        "short_threshold_pct": _finite_float(row.get("short_threshold_pct"), name="short_threshold_pct"),
        "status": "candidate_for_manual_review" if not reasons else "not_candidate",
        "reasons": reasons,
        "total_rows": total_rows,
        "actionable_rows": actionable_rows,
        "actionable_share": actionable_share,
        "positive_actionable_ratio": positive_ratio,
        "avg_net_forward_return_pct": avg_return,
        "false_positive_proxy": {
            "metric": "non_positive_actionable_ratio",
            "value": round(1.0 - positive_ratio, 8) if positive_ratio is not None else None,
            "interpretation": "share of actionable forward-return rows that were not positive for this threshold pair",
        },
    }


def _rank_key(candidate: dict[str, Any]) -> tuple[int, float, float, int, float, float]:
    status_rank = 0 if candidate.get("status") == "candidate_for_manual_review" else 1
    avg_return = _finite_float_or_none(candidate.get("avg_net_forward_return_pct"))
    positive_ratio = _finite_float_or_none(candidate.get("positive_actionable_ratio"))
    actionable_rows = int(candidate.get("actionable_rows") or 0)
    return (
        status_rank,
        -(avg_return if avg_return is not None else -9999.0),
        -(positive_ratio if positive_ratio is not None else -1.0),
        -actionable_rows,
        float(candidate.get("long_threshold_pct") or 0.0),
        float(candidate.get("short_threshold_pct") or 0.0),
    )


def build_funding_threshold_candidate_triage(
    *,
    sensitivity_report: dict[str, Any],
    min_input_rows: int = 100,
    min_actionable_rows: int = 5,
    min_actionable_share: float = 0.01,
    min_positive_ratio: float = 0.50,
    min_avg_net_forward_return_pct: float = 0.0,
) -> dict[str, Any]:
    thresholds, threshold_error = _thresholds_or_error(
        min_input_rows=min_input_rows,
        min_actionable_rows=min_actionable_rows,
        min_actionable_share=min_actionable_share,
        min_positive_ratio=min_positive_ratio,
        min_avg_net_forward_return_pct=min_avg_net_forward_return_pct,
    )
    if threshold_error is not None:
        return {
            "ok": False,
            "reason": threshold_error,
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "source_artifact_type": sensitivity_report.get("artifact_type"),
            "source_dataset_hash": sensitivity_report.get("dataset_hash"),
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }
    if not bool(sensitivity_report.get("ok")):
        return {
            "ok": False,
            "reason": str(sensitivity_report.get("reason") or "sensitivity_report_not_ok"),
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "source_artifact_type": sensitivity_report.get("artifact_type"),
            "source_dataset_hash": sensitivity_report.get("dataset_hash"),
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }

    candidates = [
        _evaluate_row(dict(row or {}), thresholds)
        for row in list(sensitivity_report.get("grid_rows") or [])
    ]
    candidates.sort(key=_rank_key)
    review_candidates = [
        row for row in candidates if row.get("status") == "candidate_for_manual_review"
    ]
    payload_for_hash = {
        "artifact_type": ARTIFACT_TYPE,
        "source_dataset_hash": sensitivity_report.get("dataset_hash"),
        "thresholds": thresholds,
        "candidates": candidates,
    }
    return {
        "ok": True,
        "reason": "ok",
        "artifact_type": ARTIFACT_TYPE,
        "research_only": True,
        "source_artifact_type": sensitivity_report.get("artifact_type"),
        "source_dataset_hash": sensitivity_report.get("dataset_hash"),
        "dataset_hash": _sha(payload_for_hash),
        "fee_bps": sensitivity_report.get("fee_bps"),
        "slippage_bps": sensitivity_report.get("slippage_bps"),
        "input_rows": sensitivity_report.get("input_rows"),
        "funding_rate_pct_range": sensitivity_report.get("funding_rate_pct_range"),
        "thresholds": thresholds,
        "evaluated_threshold_pair_count": len(candidates),
        "candidate_count": len(review_candidates),
        "candidates": candidates,
        "review_candidates": review_candidates,
        "review_required_before_use": True,
        "limitations": LIMITATIONS,
    }


def run_funding_threshold_candidate_triage(
    *,
    input_path: str | Path,
    min_input_rows: int = 100,
    min_actionable_rows: int = 5,
    min_actionable_share: float = 0.01,
    min_positive_ratio: float = 0.50,
    min_avg_net_forward_return_pct: float = 0.0,
) -> dict[str, Any]:
    thresholds, threshold_error = _thresholds_or_error(
        min_input_rows=min_input_rows,
        min_actionable_rows=min_actionable_rows,
        min_actionable_share=min_actionable_share,
        min_positive_ratio=min_positive_ratio,
        min_avg_net_forward_return_pct=min_avg_net_forward_return_pct,
    )
    if threshold_error is not None:
        return {
            "ok": False,
            "reason": threshold_error,
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }
    try:
        source = _load_source(input_path)
        return build_funding_threshold_candidate_triage(
            sensitivity_report=source,
            min_input_rows=min_input_rows,
            min_actionable_rows=min_actionable_rows,
            min_actionable_share=min_actionable_share,
            min_positive_ratio=min_positive_ratio,
            min_avg_net_forward_return_pct=min_avg_net_forward_return_pct,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }
