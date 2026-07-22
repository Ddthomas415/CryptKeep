from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from services.analytics.funding_context_price_join import _round_trip_return_pct


ARTIFACT_TYPE = "funding_threshold_sensitivity_v1"
SOURCE_ARTIFACT_TYPE = "funding_context_price_join_v1"
DEFAULT_LONG_THRESHOLDS_PCT = (0.005, 0.01, 0.02, 0.05)
DEFAULT_SHORT_THRESHOLDS_PCT = (-0.005, -0.01, -0.02, -0.05)
LIMITATIONS = [
    "threshold_sensitivity_only",
    "forward_return_only",
    "unit_size_no_position_state",
    "not_strategy_config",
    "not_campaign_evidence",
    "not_promotion_evidence",
    "not_profitability_evidence",
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


def _thresholds(values: list[float] | tuple[float, ...], *, name: str) -> list[float]:
    out = sorted({_finite_float(value, name=name) for value in values})
    if not out:
        raise ValueError(f"empty_threshold_grid:{name}")
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


def _action_for_thresholds(*, funding_rate_pct: float, long_threshold_pct: float, short_threshold_pct: float) -> str:
    if funding_rate_pct >= long_threshold_pct:
        return "sell"
    if funding_rate_pct <= short_threshold_pct:
        return "buy"
    return "hold"


def _summarize_pair(
    rows: list[dict[str, Any]],
    *,
    long_threshold_pct: float,
    short_threshold_pct: float,
    fee_bps: float,
    slippage_bps: float,
) -> dict[str, Any]:
    if long_threshold_pct <= 0.0:
        raise ValueError("invalid_threshold:long_threshold_pct")
    if short_threshold_pct >= 0.0:
        raise ValueError("invalid_threshold:short_threshold_pct")

    buy_rows = 0
    sell_rows = 0
    hold_rows = 0
    returns: list[float] = []
    for idx, row in enumerate(rows):
        rate = _finite_float(row.get("funding_rate_pct"), name=f"rows[{idx}].funding_rate_pct")
        entry = _finite_float(row.get("entry_close"), name=f"rows[{idx}].entry_close")
        exit_px = _finite_float(row.get("exit_close"), name=f"rows[{idx}].exit_close")
        action = _action_for_thresholds(
            funding_rate_pct=rate,
            long_threshold_pct=long_threshold_pct,
            short_threshold_pct=short_threshold_pct,
        )
        if action == "buy":
            buy_rows += 1
        elif action == "sell":
            sell_rows += 1
        else:
            hold_rows += 1
            continue
        net = _round_trip_return_pct(
            action=action,
            entry_px=entry,
            exit_px=exit_px,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )
        if net is not None:
            returns.append(float(net))

    actionable = buy_rows + sell_rows
    positive = sum(1 for value in returns if value > 0.0)
    return {
        "long_threshold_pct": long_threshold_pct,
        "short_threshold_pct": short_threshold_pct,
        "total_rows": len(rows),
        "buy_rows": buy_rows,
        "sell_rows": sell_rows,
        "hold_rows": hold_rows,
        "actionable_rows": actionable,
        "actionable_share": round(actionable / len(rows), 8) if rows else None,
        "positive_actionable_rows": positive,
        "positive_actionable_ratio": round(positive / len(returns), 8) if returns else None,
        "avg_net_forward_return_pct": round(sum(returns) / len(returns), 8) if returns else None,
        "min_net_forward_return_pct": round(min(returns), 8) if returns else None,
        "max_net_forward_return_pct": round(max(returns), 8) if returns else None,
    }


def run_funding_threshold_sensitivity(
    *,
    input_path: str | Path,
    long_thresholds_pct: list[float] | tuple[float, ...] = DEFAULT_LONG_THRESHOLDS_PCT,
    short_thresholds_pct: list[float] | tuple[float, ...] = DEFAULT_SHORT_THRESHOLDS_PCT,
    fee_bps: float | None = None,
    slippage_bps: float | None = None,
) -> dict[str, Any]:
    try:
        source = _load_source(input_path)
        rows = list(source.get("rows") or [])
        if not rows:
            return {
                "ok": False,
                "reason": "no_input_rows",
                "artifact_type": ARTIFACT_TYPE,
                "research_only": True,
                "limitations": LIMITATIONS,
                "rows": [],
            }
        resolved_fee_bps = _finite_float(
            source.get("fee_bps", 10.0) if fee_bps is None else fee_bps,
            name="fee_bps",
        )
        resolved_slippage_bps = _finite_float(
            source.get("slippage_bps", 5.0) if slippage_bps is None else slippage_bps,
            name="slippage_bps",
        )
        longs = _thresholds(long_thresholds_pct, name="long_threshold_pct")
        shorts = _thresholds(short_thresholds_pct, name="short_threshold_pct")
        grid = [
            _summarize_pair(
                rows,
                long_threshold_pct=long_threshold,
                short_threshold_pct=short_threshold,
                fee_bps=resolved_fee_bps,
                slippage_bps=resolved_slippage_bps,
            )
            for long_threshold in longs
            for short_threshold in shorts
        ]
    except ValueError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "artifact_type": ARTIFACT_TYPE,
            "research_only": True,
            "limitations": LIMITATIONS,
            "rows": [],
        }

    funding_rates = [_finite_float(row.get("funding_rate_pct"), name="funding_rate_pct") for row in rows]
    source_dataset_hash = str(source.get("dataset_hash") or "")
    source_artifact_hash = _sha(source)
    out: dict[str, Any] = {
        "ok": True,
        "reason": "ok",
        "artifact_type": ARTIFACT_TYPE,
        "research_only": True,
        "source_artifact_type": SOURCE_ARTIFACT_TYPE,
        "source_dataset_hash": source_dataset_hash,
        "source_artifact_hash": source_artifact_hash,
        "fee_bps": resolved_fee_bps,
        "slippage_bps": resolved_slippage_bps,
        "long_thresholds_pct": longs,
        "short_thresholds_pct": shorts,
        "input_rows": len(rows),
        "funding_rate_pct_range": {
            "min": round(min(funding_rates), 8),
            "max": round(max(funding_rates), 8),
        },
        "grid_rows": grid,
        "summary": {
            "max_actionable_rows": max((row["actionable_rows"] for row in grid), default=0),
            "current_default_actionable_rows": next(
                (
                    row["actionable_rows"]
                    for row in grid
                    if row["long_threshold_pct"] == 0.05 and row["short_threshold_pct"] == -0.01
                ),
                None,
            ),
        },
        "limitations": LIMITATIONS,
    }
    out["dataset_hash"] = _sha(
        {
            "artifact_type": ARTIFACT_TYPE,
            "source_artifact_hash": source_artifact_hash,
            "fee_bps": resolved_fee_bps,
            "slippage_bps": resolved_slippage_bps,
            "long_thresholds_pct": longs,
            "short_thresholds_pct": shorts,
            "grid_rows": grid,
        }
    )
    return out
