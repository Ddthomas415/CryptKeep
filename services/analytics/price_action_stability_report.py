from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.price_action_forward_return_join import ARTIFACT_TYPE as FORWARD_JOIN_ARTIFACT_TYPE


ARTIFACT_TYPE = "price_action_stability_report_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_forward_return_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("forward-return artifact must be a JSON object")
    return payload


def _mean(values: list[float]) -> float | None:
    return None if not values else float(sum(values) / len(values))


def _summary(rows: list[dict[str, Any]], *, min_label_count: int, baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    long_values = [float(row["forward_return_long_pct"]) for row in rows if row.get("forward_return_long_pct") is not None]
    short_values = [float(row["forward_return_short_pct"]) for row in rows if row.get("forward_return_short_pct") is not None]
    avg_long = _mean(long_values)
    avg_short = _mean(short_values)
    out: dict[str, Any] = {
        "count": len(rows),
        "meets_min_count": bool(len(rows) >= int(min_label_count)),
        "avg_forward_return_long_pct": avg_long,
        "avg_forward_return_short_pct": avg_short,
    }
    if baseline:
        baseline_long = baseline.get("avg_forward_return_long_pct")
        baseline_short = baseline.get("avg_forward_return_short_pct")
        out["delta_vs_baseline_long_pct"] = (
            None
            if avg_long is None or baseline_long is None
            else float(avg_long - float(baseline_long))
        )
        out["delta_vs_baseline_short_pct"] = (
            None
            if avg_short is None or baseline_short is None
            else float(avg_short - float(baseline_short))
        )
    return out


def _window_rows(rows: list[dict[str, Any]], *, window_size_rows: int) -> list[list[dict[str, Any]]]:
    size = max(1, int(window_size_rows))
    ordered = sorted(rows, key=lambda row: (int(row.get("ts_ms") or 0), str(row.get("ts") or "")))
    return [ordered[idx : idx + size] for idx in range(0, len(ordered), size)]


def _label_groups(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for label in list(row.get("labels") or []):
            key = str(label or "").strip()
            if key:
                grouped[key].append(row)
    return dict(grouped)


def _dominant_side(
    *,
    avg_long_delta: float | None,
    avg_short_delta: float | None,
    long_positive_ratio: float | None,
    short_positive_ratio: float | None,
    consistency_threshold: float,
) -> str:
    long_ok = (
        avg_long_delta is not None
        and avg_long_delta > 0.0
        and long_positive_ratio is not None
        and long_positive_ratio >= consistency_threshold
    )
    short_ok = (
        avg_short_delta is not None
        and avg_short_delta > 0.0
        and short_positive_ratio is not None
        and short_positive_ratio >= consistency_threshold
    )
    if long_ok and short_ok:
        if abs(float(avg_long_delta)) > abs(float(avg_short_delta)):
            return "long"
        if abs(float(avg_short_delta)) > abs(float(avg_long_delta)):
            return "short"
        return "mixed"
    if long_ok:
        return "long"
    if short_ok:
        return "short"
    return "none"


def build_price_action_stability_report(
    *,
    forward_return_artifact: dict[str, Any],
    window_size_rows: int = 100,
    min_windows: int = 3,
    min_label_count: int = 5,
    consistency_threshold: float = 0.6,
) -> dict[str, Any]:
    if str(forward_return_artifact.get("artifact_type") or "") != FORWARD_JOIN_ARTIFACT_TYPE:
        return {
            "artifact_type": ARTIFACT_TYPE,
            "ok": False,
            "reason": "unsupported_forward_return_artifact",
            "research_only": True,
            "not_strategy_config": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
            "not_profitability_evidence": True,
            "label_stability": {},
        }
    if not bool(forward_return_artifact.get("ok")):
        return {
            "artifact_type": ARTIFACT_TYPE,
            "ok": False,
            "reason": str(forward_return_artifact.get("reason") or "forward_return_artifact_not_ok"),
            "research_only": True,
            "not_strategy_config": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
            "not_profitability_evidence": True,
            "forward_return_artifact_hash": str(forward_return_artifact.get("artifact_hash") or ""),
            "dataset_hash": str(forward_return_artifact.get("dataset_hash") or ""),
            "label_stability": {},
        }

    rows = [dict(row) for row in list(forward_return_artifact.get("rows") or []) if isinstance(row, dict)]
    windows = _window_rows(rows, window_size_rows=window_size_rows)
    threshold = float(consistency_threshold)
    if not math.isfinite(threshold) or threshold < 0.0 or threshold > 1.0:
        raise ValueError("invalid_numeric:consistency_threshold")

    window_reports: list[dict[str, Any]] = []
    label_windows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for idx, window in enumerate(windows):
        baseline = _summary(window, min_label_count=min_label_count)
        labels: dict[str, dict[str, Any]] = {}
        for label, label_rows in sorted(_label_groups(window).items()):
            summary = _summary(label_rows, min_label_count=min_label_count, baseline=baseline)
            labels[label] = summary
            if summary.get("meets_min_count"):
                label_windows[label].append(summary)
        window_reports.append(
            {
                "window_index": idx,
                "row_count": len(window),
                "start_ts_ms": None if not window else int(window[0].get("ts_ms") or 0),
                "end_ts_ms": None if not window else int(window[-1].get("ts_ms") or 0),
                "baseline": baseline,
                "labels": labels,
            }
        )

    label_stability: dict[str, dict[str, Any]] = {}
    for label, summaries in sorted(label_windows.items()):
        long_deltas = [
            float(item["delta_vs_baseline_long_pct"])
            for item in summaries
            if item.get("delta_vs_baseline_long_pct") is not None
        ]
        short_deltas = [
            float(item["delta_vs_baseline_short_pct"])
            for item in summaries
            if item.get("delta_vs_baseline_short_pct") is not None
        ]
        avg_long_delta = _mean(long_deltas)
        avg_short_delta = _mean(short_deltas)
        long_positive_ratio = None if not long_deltas else float(sum(1 for value in long_deltas if value > 0.0) / len(long_deltas))
        short_positive_ratio = None if not short_deltas else float(sum(1 for value in short_deltas if value > 0.0) / len(short_deltas))
        dominant = _dominant_side(
            avg_long_delta=avg_long_delta,
            avg_short_delta=avg_short_delta,
            long_positive_ratio=long_positive_ratio,
            short_positive_ratio=short_positive_ratio,
            consistency_threshold=threshold,
        )
        label_stability[label] = {
            "windows_meeting_min_count": len(summaries),
            "meets_min_windows": bool(len(summaries) >= int(min_windows)),
            "total_label_rows": int(sum(int(item.get("count") or 0) for item in summaries)),
            "avg_delta_vs_baseline_long_pct": avg_long_delta,
            "avg_delta_vs_baseline_short_pct": avg_short_delta,
            "positive_delta_long_window_ratio": long_positive_ratio,
            "positive_delta_short_window_ratio": short_positive_ratio,
            "dominant_observed_side": dominant,
            "stable_observation": bool(len(summaries) >= int(min_windows) and dominant != "none"),
        }

    payload_for_hash = {
        "forward_return_artifact_hash": str(forward_return_artifact.get("artifact_hash") or ""),
        "dataset_hash": str(forward_return_artifact.get("dataset_hash") or ""),
        "window_size_rows": int(window_size_rows),
        "min_windows": int(min_windows),
        "min_label_count": int(min_label_count),
        "consistency_threshold": threshold,
        "label_stability": label_stability,
        "windows": window_reports,
    }
    return {
        "artifact_type": ARTIFACT_TYPE,
        "ok": True,
        "research_only": True,
        "not_strategy_config": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_profitability_evidence": True,
        "generated_at": _utc_now(),
        "venue": str(forward_return_artifact.get("venue") or ""),
        "symbol": str(forward_return_artifact.get("symbol") or ""),
        "timeframe": str(forward_return_artifact.get("timeframe") or ""),
        "dataset_hash": str(forward_return_artifact.get("dataset_hash") or ""),
        "label_artifact_hash": str(forward_return_artifact.get("label_artifact_hash") or ""),
        "forward_return_artifact_hash": str(forward_return_artifact.get("artifact_hash") or ""),
        "artifact_hash": _sha(payload_for_hash),
        "row_count": len(rows),
        "window_count": len(window_reports),
        "window_size_rows": int(window_size_rows),
        "min_windows": int(min_windows),
        "min_label_count": int(min_label_count),
        "consistency_threshold": threshold,
        "label_stability": label_stability,
        "windows": window_reports,
        "limitations": [
            "descriptive_window_stability_only",
            "not_strategy_selection",
            "does_not_authorize_confirmation_filters",
            "requires_separate_review_before_strategy_use",
        ],
    }


def run_price_action_stability_report(
    *,
    forward_return_artifact_path: str | Path,
    window_size_rows: int = 100,
    min_windows: int = 3,
    min_label_count: int = 5,
    consistency_threshold: float = 0.6,
) -> dict[str, Any]:
    return build_price_action_stability_report(
        forward_return_artifact=load_forward_return_artifact(forward_return_artifact_path),
        window_size_rows=window_size_rows,
        min_windows=min_windows,
        min_label_count=min_label_count,
        consistency_threshold=consistency_threshold,
    )
