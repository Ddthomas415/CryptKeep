from __future__ import annotations

import hashlib
import json
from typing import Any

from services.analytics.price_action_window_stability import (
    run_price_action_window_stability,
)
from services.backtest.price_action_context import LIMITATION_FLAGS
from services.market_data.symbol_router import normalize_symbol, normalize_venue


ARTIFACT_TYPE = "price_action_candidate_triage_v1"


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _f(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def _i(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _thresholds(
    *,
    min_windows: int,
    min_sample_size: int,
    min_avg_delta_pct: float,
    min_outperform_ratio: float,
    max_underperform_ratio: float,
) -> dict[str, Any]:
    return {
        "min_windows": max(1, int(min_windows)),
        "min_sample_size": max(1, int(min_sample_size)),
        "min_avg_delta_vs_unconditioned_pct": float(min_avg_delta_pct),
        "min_outperform_window_ratio": min(1.0, max(0.0, float(min_outperform_ratio))),
        "max_underperform_window_ratio": min(1.0, max(0.0, float(max_underperform_ratio))),
    }


def _side_eval(label: str, side: str, row: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    window_count = _i(row.get("window_count"))
    sample_size = _i(row.get(f"{side}_sample_size"))
    avg_delta = _f(row.get(f"avg_{side}_delta_vs_unconditioned_pct"))
    outperform_ratio = _f(row.get(f"{side}_outperform_window_ratio"))
    underperform_ratio = _f(row.get(f"{side}_underperform_window_ratio"))
    reasons: list[str] = []

    if window_count < int(thresholds["min_windows"]):
        reasons.append("insufficient_windows")
    if sample_size < int(thresholds["min_sample_size"]):
        reasons.append("insufficient_sample_size")
    if avg_delta is None:
        reasons.append("missing_avg_delta")
    elif avg_delta < float(thresholds["min_avg_delta_vs_unconditioned_pct"]):
        reasons.append("avg_delta_below_threshold")
    if outperform_ratio is None:
        reasons.append("missing_outperform_ratio")
    elif outperform_ratio < float(thresholds["min_outperform_window_ratio"]):
        reasons.append("outperform_ratio_below_threshold")
    if underperform_ratio is None:
        reasons.append("missing_underperform_ratio")
    elif underperform_ratio > float(thresholds["max_underperform_window_ratio"]):
        reasons.append("underperform_ratio_above_threshold")

    status = "candidate_for_manual_review" if not reasons else "not_candidate"
    return {
        "label": str(label),
        "side": side,
        "status": status,
        "reasons": reasons,
        "window_count": window_count,
        "sample_size": sample_size,
        "avg_delta_vs_unconditioned_pct": avg_delta,
        "outperform_window_ratio": outperform_ratio,
        "underperform_window_ratio": underperform_ratio,
        "false_positive_proxy": {
            "metric": "underperform_window_ratio",
            "value": underperform_ratio,
            "interpretation": "share of evaluated windows where the label underperformed the unconditioned baseline for this side",
        },
    }


def _rank_key(candidate: dict[str, Any]) -> tuple[int, float, float, int, str]:
    status_rank = 0 if candidate.get("status") == "candidate_for_manual_review" else 1
    delta = _f(candidate.get("avg_delta_vs_unconditioned_pct"))
    outperform = _f(candidate.get("outperform_window_ratio"))
    sample = _i(candidate.get("sample_size"))
    return (
        status_rank,
        -(delta if delta is not None else -9999.0),
        -(outperform if outperform is not None else -1.0),
        -sample,
        str(candidate.get("label") or ""),
    )


def build_price_action_candidate_triage(
    *,
    stability_report: dict[str, Any],
    min_windows: int = 2,
    min_sample_size: int = 10,
    min_avg_delta_pct: float = 0.0,
    min_outperform_ratio: float = 0.60,
    max_underperform_ratio: float = 0.40,
) -> dict[str, Any]:
    thresholds = _thresholds(
        min_windows=min_windows,
        min_sample_size=min_sample_size,
        min_avg_delta_pct=min_avg_delta_pct,
        min_outperform_ratio=min_outperform_ratio,
        max_underperform_ratio=max_underperform_ratio,
    )
    if not bool(stability_report.get("ok")):
        return {
            "ok": False,
            "reason": str(stability_report.get("reason") or "stability_report_not_ok"),
            "artifact_type": ARTIFACT_TYPE,
            **LIMITATION_FLAGS,
            "limitation_flags": dict(LIMITATION_FLAGS),
            "source_artifact_type": stability_report.get("artifact_type"),
            "source_dataset_hash": stability_report.get("dataset_hash"),
            "thresholds": thresholds,
            "candidate_count": 0,
            "candidates": [],
            "review_required_before_use": True,
            "limitations": [
                "research_only",
                "triage_only",
                "not_strategy_config",
                "not_campaign_evidence",
                "not_promotion_evidence",
                "not_profitability_evidence",
                "not_activation_decision",
            ],
        }

    candidates: list[dict[str, Any]] = []
    for label, row in sorted(dict(stability_report.get("label_stability") or {}).items()):
        candidates.append(_side_eval(str(label), "long", dict(row or {}), thresholds))
        candidates.append(_side_eval(str(label), "short", dict(row or {}), thresholds))
    candidates.sort(key=_rank_key)
    accepted = [c for c in candidates if c["status"] == "candidate_for_manual_review"]
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
        **LIMITATION_FLAGS,
        "limitation_flags": dict(LIMITATION_FLAGS),
        "venue": stability_report.get("venue"),
        "symbol": stability_report.get("symbol"),
        "timeframe": stability_report.get("timeframe"),
        "source_artifact_type": stability_report.get("artifact_type"),
        "source_dataset_hash": stability_report.get("dataset_hash"),
        "dataset_hash": _sha(payload_for_hash),
        "thresholds": thresholds,
        "evaluated_side_count": len(candidates),
        "candidate_count": len(accepted),
        "candidates": candidates,
        "review_candidates": accepted,
        "review_required_before_use": True,
        "limitations": [
            "research_only",
            "triage_only",
            "not_strategy_config",
            "not_campaign_evidence",
            "not_promotion_evidence",
            "not_profitability_evidence",
            "not_activation_decision",
        ],
    }


def run_price_action_candidate_triage(
    *,
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
    db_path: str | None = None,
    window_bars: int = 120,
    step_bars: int | None = None,
    min_windows: int = 2,
    horizon_bars: int = 1,
    min_labeled_rows: int = 1,
    fee_bps: float | None = None,
    slippage_bps: float | None = None,
    label_config: dict[str, Any] | None = None,
    min_sample_size: int = 10,
    min_avg_delta_pct: float = 0.0,
    min_outperform_ratio: float = 0.60,
    max_underperform_ratio: float = 0.40,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "venue": normalize_venue(venue),
        "symbol": normalize_symbol(symbol),
        "timeframe": str(timeframe),
        "limit": int(limit),
        "since_ms": since_ms,
        "db_path": db_path,
        "window_bars": int(window_bars),
        "step_bars": step_bars,
        "min_windows": int(min_windows),
        "horizon_bars": int(horizon_bars),
        "min_labeled_rows": int(min_labeled_rows),
        "label_config": label_config,
    }
    if fee_bps is not None:
        kwargs["fee_bps"] = float(fee_bps)
    if slippage_bps is not None:
        kwargs["slippage_bps"] = float(slippage_bps)
    stability = run_price_action_window_stability(**kwargs)
    return build_price_action_candidate_triage(
        stability_report=stability,
        min_windows=min_windows,
        min_sample_size=min_sample_size,
        min_avg_delta_pct=min_avg_delta_pct,
        min_outperform_ratio=min_outperform_ratio,
        max_underperform_ratio=max_underperform_ratio,
    )
