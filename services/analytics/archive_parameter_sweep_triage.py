from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ARTIFACT_TYPE = "archive_parameter_sweep_triage_v1"
SOURCE_ARTIFACT_TYPE = "archive_backed_parameter_sweep_v1"
LIMITATIONS = [
    "research_only",
    "triage_only",
    "sweep_candidate_review_only",
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


def _non_negative_int(value: Any, *, name: str) -> int:
    try:
        out = int(float(value))
    except Exception as exc:
        raise ValueError(f"invalid_integer:{name}") from exc
    if out < 0:
        raise ValueError(f"invalid_integer:{name}")
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
    rows = payload.get("ranked_variants")
    if not isinstance(rows, list):
        raise ValueError("input_ranked_variants_missing")
    return payload


def _thresholds(
    *,
    min_successful_variants: int,
    min_window_count: int,
    min_closed_trades: int,
    min_non_negative_window_ratio: float,
    min_avg_test_return_pct: float,
    max_avg_test_drawdown_pct: float,
) -> dict[str, Any]:
    return {
        "min_successful_variants": max(1, int(min_successful_variants)),
        "min_window_count": max(1, int(min_window_count)),
        "min_total_test_closed_trades": max(0, int(min_closed_trades)),
        "min_non_negative_test_window_ratio": _ratio(
            min_non_negative_window_ratio,
            name="min_non_negative_test_window_ratio",
        ),
        "min_avg_test_return_pct": _finite_float(min_avg_test_return_pct, name="min_avg_test_return_pct"),
        "max_avg_test_drawdown_pct": _finite_float(max_avg_test_drawdown_pct, name="max_avg_test_drawdown_pct"),
    }


def _thresholds_or_error(
    *,
    min_successful_variants: int,
    min_window_count: int,
    min_closed_trades: int,
    min_non_negative_window_ratio: float,
    min_avg_test_return_pct: float,
    max_avg_test_drawdown_pct: float,
) -> tuple[dict[str, Any], str | None]:
    try:
        return (
            _thresholds(
                min_successful_variants=min_successful_variants,
                min_window_count=min_window_count,
                min_closed_trades=min_closed_trades,
                min_non_negative_window_ratio=min_non_negative_window_ratio,
                min_avg_test_return_pct=min_avg_test_return_pct,
                max_avg_test_drawdown_pct=max_avg_test_drawdown_pct,
            ),
            None,
        )
    except ValueError as exc:
        return ({}, str(exc))


def _evaluate_variant(row: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    score = dict(row.get("score") or {})
    window_count = _non_negative_int(
        score.get("window_count", row.get("window_count", 0)),
        name="window_count",
    )
    closed_trades = _non_negative_int(
        score.get("total_test_closed_trades", 0),
        name="total_test_closed_trades",
    )
    non_negative_ratio = _finite_float_or_none(score.get("non_negative_test_window_ratio"))
    avg_return = _finite_float_or_none(score.get("avg_test_return_pct"))
    avg_drawdown = _finite_float_or_none(score.get("avg_test_max_drawdown_pct"))
    reasons: list[str] = []

    if not bool(row.get("ok")):
        reasons.append("variant_not_ok")
    if window_count < int(thresholds["min_window_count"]):
        reasons.append("insufficient_windows")
    if closed_trades < int(thresholds["min_total_test_closed_trades"]):
        reasons.append("insufficient_closed_trades")
    if non_negative_ratio is None:
        reasons.append("missing_non_negative_window_ratio")
    elif non_negative_ratio < float(thresholds["min_non_negative_test_window_ratio"]):
        reasons.append("non_negative_window_ratio_below_threshold")
    if avg_return is None:
        reasons.append("missing_avg_test_return_pct")
    elif avg_return < float(thresholds["min_avg_test_return_pct"]):
        reasons.append("avg_test_return_below_threshold")
    if avg_drawdown is None:
        reasons.append("missing_avg_test_max_drawdown_pct")
    elif avg_drawdown > float(thresholds["max_avg_test_drawdown_pct"]):
        reasons.append("avg_test_drawdown_above_threshold")

    return {
        "variant_id": str(row.get("variant_id") or ""),
        "rank": _non_negative_int(row.get("rank", 0), name="rank"),
        "status": "candidate_for_manual_review" if not reasons else "not_candidate",
        "reasons": reasons,
        "strategy": str(row.get("strategy") or ""),
        "parameters": dict(row.get("parameters") or {}),
        "config_hash": str(row.get("config_hash") or ""),
        "dataset_hash": str(row.get("dataset_hash") or ""),
        "window_count": window_count,
        "total_test_closed_trades": closed_trades,
        "non_negative_test_window_ratio": non_negative_ratio,
        "avg_test_return_pct": avg_return,
        "avg_test_max_drawdown_pct": avg_drawdown,
        "research_score": _finite_float_or_none(score.get("research_score")),
        "false_positive_proxy": {
            "metric": "negative_test_window_ratio",
            "value": round(1.0 - non_negative_ratio, 8) if non_negative_ratio is not None else None,
            "interpretation": "share of walk-forward test windows with negative return for this variant",
        },
    }


def _rank_key(candidate: dict[str, Any]) -> tuple[int, float, float, int, int, str]:
    status_rank = 0 if candidate.get("status") == "candidate_for_manual_review" else 1
    score = _finite_float_or_none(candidate.get("research_score"))
    non_negative = _finite_float_or_none(candidate.get("non_negative_test_window_ratio"))
    closed = int(candidate.get("total_test_closed_trades") or 0)
    rank = int(candidate.get("rank") or 0)
    return (
        status_rank,
        -(score if score is not None else -9999.0),
        -(non_negative if non_negative is not None else -1.0),
        -closed,
        rank,
        str(candidate.get("variant_id") or ""),
    )


def build_archive_parameter_sweep_triage(
    *,
    sweep_report: dict[str, Any],
    min_successful_variants: int = 1,
    min_window_count: int = 2,
    min_closed_trades: int = 1,
    min_non_negative_window_ratio: float = 0.50,
    min_avg_test_return_pct: float = 0.0,
    max_avg_test_drawdown_pct: float = 100.0,
) -> dict[str, Any]:
    thresholds, threshold_error = _thresholds_or_error(
        min_successful_variants=min_successful_variants,
        min_window_count=min_window_count,
        min_closed_trades=min_closed_trades,
        min_non_negative_window_ratio=min_non_negative_window_ratio,
        min_avg_test_return_pct=min_avg_test_return_pct,
        max_avg_test_drawdown_pct=max_avg_test_drawdown_pct,
    )
    if threshold_error is not None:
        return {
            "ok": False,
            "reason": threshold_error,
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "source_artifact_type": sweep_report.get("artifact_type"),
            "source_dataset_hashes": [],
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }
    if not bool(sweep_report.get("ok")):
        return {
            "ok": False,
            "reason": str(sweep_report.get("reason") or "sweep_report_not_ok"),
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "source_artifact_type": sweep_report.get("artifact_type"),
            "source_dataset_hashes": list((sweep_report.get("dataset_summary") or {}).get("dataset_hashes") or []),
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": LIMITATIONS,
        }

    candidates = [_evaluate_variant(dict(row or {}), thresholds) for row in list(sweep_report.get("ranked_variants") or [])]
    candidates.sort(key=_rank_key)
    review_candidates = [
        row for row in candidates if row.get("status") == "candidate_for_manual_review"
    ]
    source_dataset_hashes = list((sweep_report.get("dataset_summary") or {}).get("dataset_hashes") or [])
    payload_for_hash = {
        "artifact_type": ARTIFACT_TYPE,
        "source_dataset_hashes": source_dataset_hashes,
        "thresholds": thresholds,
        "candidates": candidates,
    }
    ok = len(review_candidates) >= int(thresholds["min_successful_variants"])
    return {
        "ok": ok,
        "reason": "ok" if ok else "insufficient_review_candidates",
        "artifact_type": ARTIFACT_TYPE,
        "research_only": True,
        "source_artifact_type": sweep_report.get("artifact_type"),
        "source_dataset_hashes": source_dataset_hashes,
        "source_artifact_hash": _sha(sweep_report),
        "dataset_hash": _sha(payload_for_hash),
        "venue": sweep_report.get("venue"),
        "symbol": sweep_report.get("symbol"),
        "timeframe": sweep_report.get("timeframe"),
        "variant_count": int(sweep_report.get("variant_count") or len(candidates)),
        "successful_variant_count": int(sweep_report.get("successful_variant_count") or 0),
        "thresholds": thresholds,
        "evaluated_variant_count": len(candidates),
        "candidate_count": len(review_candidates),
        "candidates": candidates,
        "review_candidates": review_candidates,
        "source_cost_assumptions_present": bool("fee_bps" in sweep_report and "slippage_bps" in sweep_report),
        "cost_assumption_note": (
            "This triage consumes source sweep metrics as-is and does not verify "
            "the sweep's fee/slippage assumptions."
        ),
        "review_required_before_use": True,
        "limitations": LIMITATIONS,
    }


def run_archive_parameter_sweep_triage(
    *,
    input_path: str | Path,
    min_successful_variants: int = 1,
    min_window_count: int = 2,
    min_closed_trades: int = 1,
    min_non_negative_window_ratio: float = 0.50,
    min_avg_test_return_pct: float = 0.0,
    max_avg_test_drawdown_pct: float = 100.0,
) -> dict[str, Any]:
    try:
        source = _load_source(input_path)
        return build_archive_parameter_sweep_triage(
            sweep_report=source,
            min_successful_variants=min_successful_variants,
            min_window_count=min_window_count,
            min_closed_trades=min_closed_trades,
            min_non_negative_window_ratio=min_non_negative_window_ratio,
            min_avg_test_return_pct=min_avg_test_return_pct,
            max_avg_test_drawdown_pct=max_avg_test_drawdown_pct,
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
