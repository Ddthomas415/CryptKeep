from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from services.analytics.funding_threshold_sensitivity import (
    DEFAULT_LONG_THRESHOLDS_PCT,
    DEFAULT_SHORT_THRESHOLDS_PCT,
    _summarize_pair,
    _thresholds,
)


ARTIFACT_TYPE = "funding_threshold_window_stability_v1"
SOURCE_ARTIFACT_TYPE = "funding_context_price_join_v1"
LIMITATIONS = [
    "research_only",
    "window_stability_only",
    "forward_return_only",
    "unit_size_no_position_state",
    "not_strategy_config",
    "not_campaign_evidence",
    "not_promotion_evidence",
    "not_profitability_evidence",
    "not_activation_decision",
]


def _sha(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _load_source(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("input_unreadable") from exc
    if not isinstance(payload, dict):
        raise ValueError("input_not_object")
    if payload.get("artifact_type") != SOURCE_ARTIFACT_TYPE:
        raise ValueError("unsupported_input_artifact_type")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("input_rows_missing")
    return payload


def _cost_from_source(source: dict[str, Any]) -> tuple[float, float]:
    if "fee_bps" not in source or "slippage_bps" not in source:
        raise ValueError("source_cost_assumptions_missing")
    return (
        _finite_float(source.get("fee_bps"), name="source.fee_bps"),
        _finite_float(source.get("slippage_bps"), name="source.slippage_bps"),
    )


def _windows(rows: list[dict[str, Any]], *, window_rows: int, step_rows: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    size = max(1, int(window_rows))
    step = max(1, int(step_rows))
    for start in range(0, max(len(rows) - size + 1, 0), step):
        chunk = rows[start : start + size]
        if len(chunk) != size:
            continue
        out.append(
            {
                "window_index": len(out),
                "start_row": start,
                "end_row_exclusive": start + size,
                "row_count": len(chunk),
                "start_capture_ts": chunk[0].get("capture_ts"),
                "end_capture_ts": chunk[-1].get("capture_ts"),
                "rows": chunk,
            }
        )
    return out


def _summarize_threshold_windows(
    windows: list[dict[str, Any]],
    *,
    long_threshold_pct: float,
    short_threshold_pct: float,
    fee_bps: float,
    slippage_bps: float,
) -> dict[str, Any]:
    window_rows = [
        _summarize_pair(
            list(window.get("rows") or []),
            long_threshold_pct=long_threshold_pct,
            short_threshold_pct=short_threshold_pct,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )
        | {
            "window_index": int(window.get("window_index") or 0),
            "start_row": int(window.get("start_row") or 0),
            "end_row_exclusive": int(window.get("end_row_exclusive") or 0),
            "start_capture_ts": window.get("start_capture_ts"),
            "end_capture_ts": window.get("end_capture_ts"),
        }
        for window in windows
    ]
    actionable_windows = [row for row in window_rows if int(row.get("actionable_rows") or 0) > 0]
    positive_windows = [
        row
        for row in actionable_windows
        if (_finite_float_or_none(row.get("avg_net_forward_return_pct")) or 0.0) > 0.0
    ]
    avg_returns = [
        value
        for value in (_finite_float_or_none(row.get("avg_net_forward_return_pct")) for row in actionable_windows)
        if value is not None
    ]
    actionable_counts = [int(row.get("actionable_rows") or 0) for row in window_rows]
    actionable_shares = [
        value
        for value in (_finite_float_or_none(row.get("actionable_share")) for row in window_rows)
        if value is not None
    ]
    window_count = len(window_rows)
    return {
        "long_threshold_pct": long_threshold_pct,
        "short_threshold_pct": short_threshold_pct,
        "window_count": window_count,
        "windows_with_actionable_rows": len(actionable_windows),
        "actionable_window_ratio": round(len(actionable_windows) / window_count, 8) if window_count else None,
        "positive_actionable_window_ratio": (
            round(len(positive_windows) / len(actionable_windows), 8) if actionable_windows else None
        ),
        "avg_actionable_rows_per_window": (
            round(sum(actionable_counts) / len(actionable_counts), 8) if actionable_counts else None
        ),
        "avg_actionable_share": (
            round(sum(actionable_shares) / len(actionable_shares), 8) if actionable_shares else None
        ),
        "avg_net_forward_return_pct_across_actionable_windows": (
            round(sum(avg_returns) / len(avg_returns), 8) if avg_returns else None
        ),
        "worst_window_avg_net_forward_return_pct": round(min(avg_returns), 8) if avg_returns else None,
        "window_rows": window_rows,
    }


def run_funding_threshold_window_stability(
    *,
    input_path: str | Path,
    long_thresholds_pct: list[float] | tuple[float, ...] = DEFAULT_LONG_THRESHOLDS_PCT,
    short_thresholds_pct: list[float] | tuple[float, ...] = DEFAULT_SHORT_THRESHOLDS_PCT,
    window_rows: int = 100,
    step_rows: int | None = None,
    min_windows: int = 2,
) -> dict[str, Any]:
    try:
        source = _load_source(input_path)
        rows = list(source.get("rows") or [])
        if not rows:
            raise ValueError("no_input_rows")
        fee_bps, slippage_bps = _cost_from_source(source)
        longs = _thresholds(long_thresholds_pct, name="long_threshold_pct")
        shorts = _thresholds(short_thresholds_pct, name="short_threshold_pct")
        resolved_window_rows = max(1, int(window_rows))
        resolved_step_rows = max(1, int(step_rows if step_rows is not None else resolved_window_rows))
        resolved_min_windows = max(1, int(min_windows))
        windows = _windows(rows, window_rows=resolved_window_rows, step_rows=resolved_step_rows)
        if len(windows) < resolved_min_windows:
            return {
                "ok": False,
                "reason": "insufficient_windows",
                "artifact_type": ARTIFACT_TYPE,
                "research_only": True,
                "source_artifact_type": SOURCE_ARTIFACT_TYPE,
                "source_dataset_hash": source.get("dataset_hash"),
                "input_rows": len(rows),
                "window_rows": resolved_window_rows,
                "step_rows": resolved_step_rows,
                "min_windows": resolved_min_windows,
                "window_count": len(windows),
                "threshold_stability": [],
                "limitations": LIMITATIONS,
            }
        stability = [
            _summarize_threshold_windows(
                windows,
                long_threshold_pct=long_threshold,
                short_threshold_pct=short_threshold,
                fee_bps=fee_bps,
                slippage_bps=slippage_bps,
            )
            for long_threshold in longs
            for short_threshold in shorts
        ]
    except (ValueError, TypeError) as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "source_artifact_type": SOURCE_ARTIFACT_TYPE,
            "threshold_stability": [],
            "limitations": LIMITATIONS,
        }

    source_hash = _sha(source)
    dataset_hash = _sha(
        {
            "artifact_type": ARTIFACT_TYPE,
            "source_artifact_hash": source_hash,
            "long_thresholds_pct": longs,
            "short_thresholds_pct": shorts,
            "window_rows": resolved_window_rows,
            "step_rows": resolved_step_rows,
            "threshold_stability": stability,
        }
    )
    return {
        "ok": True,
        "reason": "ok",
        "artifact_type": ARTIFACT_TYPE,
        "research_only": True,
        "source_artifact_type": SOURCE_ARTIFACT_TYPE,
        "source_dataset_hash": source.get("dataset_hash"),
        "source_artifact_hash": source_hash,
        "dataset_hash": dataset_hash,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "input_rows": len(rows),
        "window_rows": resolved_window_rows,
        "step_rows": resolved_step_rows,
        "min_windows": resolved_min_windows,
        "window_count": len(windows),
        "long_thresholds_pct": longs,
        "short_thresholds_pct": shorts,
        "threshold_stability": stability,
        "limitations": LIMITATIONS,
    }
