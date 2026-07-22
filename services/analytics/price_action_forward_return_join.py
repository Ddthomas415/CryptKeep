from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.price_action_context_labels import ARTIFACT_TYPE as LABEL_ARTIFACT_TYPE
from services.execution.fill_model import apply_fee_slippage


ARTIFACT_TYPE = "price_action_forward_return_join_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_label_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("label artifact must be a JSON object")
    return payload


def _finite_float(value: Any, *, name: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValueError(f"invalid_numeric:{name}") from exc
    if not math.isfinite(out):
        raise ValueError(f"invalid_numeric:{name}")
    return out


def _round_trip_return_pct(
    *,
    side: str,
    entry_px: float,
    exit_px: float,
    fee_bps: float,
    slippage_bps: float,
) -> float | None:
    if entry_px <= 0.0 or exit_px <= 0.0:
        return None
    s = str(side or "").lower().strip()
    if s == "long":
        entry = apply_fee_slippage(mid_px=entry_px, side="buy", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        exit_fill = apply_fee_slippage(mid_px=exit_px, side="sell", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        basis = entry.notional + entry.fee
        profit = (exit_fill.notional - exit_fill.fee) - basis
    elif s == "short":
        entry = apply_fee_slippage(mid_px=entry_px, side="sell", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        exit_fill = apply_fee_slippage(mid_px=exit_px, side="buy", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        basis = entry.notional + entry.fee
        profit = (entry.notional - entry.fee) - (exit_fill.notional + exit_fill.fee)
    else:
        return None
    if basis <= 0.0:
        return None
    return float((profit / basis) * 100.0)


def _active_label_keys(row: dict[str, Any]) -> list[str]:
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    keys: list[str] = []
    for name, value in labels.items():
        if value is None or value == "":
            continue
        keys.append(f"{name}:{value}")
    return sorted(keys)


def _summary(rows: list[dict[str, Any]], *, min_count: int, baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    count = len(rows)
    longs = [float(row["forward_return_long_pct"]) for row in rows if row.get("forward_return_long_pct") is not None]
    shorts = [float(row["forward_return_short_pct"]) for row in rows if row.get("forward_return_short_pct") is not None]
    avg_long = (sum(longs) / len(longs)) if longs else None
    avg_short = (sum(shorts) / len(shorts)) if shorts else None
    out = {
        "count": int(count),
        "meets_min_count": bool(count >= int(min_count)),
        "avg_forward_return_long_pct": None if avg_long is None else float(avg_long),
        "avg_forward_return_short_pct": None if avg_short is None else float(avg_short),
        "positive_long_ratio": None if not longs else float(sum(1 for value in longs if value > 0.0) / len(longs)),
        "positive_short_ratio": None if not shorts else float(sum(1 for value in shorts if value > 0.0) / len(shorts)),
    }
    if baseline:
        base_long = baseline.get("avg_forward_return_long_pct")
        base_short = baseline.get("avg_forward_return_short_pct")
        out["delta_vs_baseline_long_pct"] = None if avg_long is None or base_long is None else float(avg_long - float(base_long))
        out["delta_vs_baseline_short_pct"] = None if avg_short is None or base_short is None else float(avg_short - float(base_short))
    return out


def build_price_action_forward_return_join(
    *,
    label_artifact: dict[str, Any],
    horizon_bars: int = 1,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    min_label_count: int = 5,
    min_forward_rows: int = 1,
) -> dict[str, Any]:
    if str(label_artifact.get("artifact_type") or "") != LABEL_ARTIFACT_TYPE:
        return {
            "artifact_type": ARTIFACT_TYPE,
            "ok": False,
            "reason": "unsupported_label_artifact",
            "research_only": True,
            "not_strategy_config": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
            "not_profitability_evidence": True,
            "rows": [],
        }
    if not bool(label_artifact.get("ok")):
        return {
            "artifact_type": ARTIFACT_TYPE,
            "ok": False,
            "reason": str(label_artifact.get("reason") or "label_artifact_not_ok"),
            "research_only": True,
            "not_strategy_config": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
            "not_profitability_evidence": True,
            "label_artifact_hash": str(label_artifact.get("artifact_hash") or ""),
            "dataset_hash": str(label_artifact.get("dataset_hash") or ""),
            "rows": [],
        }

    labels = [dict(row) for row in list(label_artifact.get("labels") or []) if isinstance(row, dict)]
    horizon = max(1, int(horizon_bars))
    fee = _finite_float(fee_bps, name="fee_bps")
    slippage = _finite_float(slippage_bps, name="slippage_bps")
    joined: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for idx, row in enumerate(labels):
        exit_idx = idx + horizon
        if exit_idx >= len(labels):
            continue
        entry_px = _finite_float(row.get("close"), name="close")
        exit_px = _finite_float(labels[exit_idx].get("close"), name="exit_close")
        long_return = _round_trip_return_pct(
            side="long",
            entry_px=entry_px,
            exit_px=exit_px,
            fee_bps=fee,
            slippage_bps=slippage,
        )
        short_return = _round_trip_return_pct(
            side="short",
            entry_px=entry_px,
            exit_px=exit_px,
            fee_bps=fee,
            slippage_bps=slippage,
        )
        active_labels = _active_label_keys(row)
        out_row = {
            "ts_ms": int(row.get("ts_ms") or 0),
            "ts": str(row.get("ts") or ""),
            "exit_ts_ms": int(labels[exit_idx].get("ts_ms") or 0),
            "exit_ts": str(labels[exit_idx].get("ts") or ""),
            "entry_close": float(entry_px),
            "exit_close": float(exit_px),
            "horizon_bars": int(horizon),
            "labels": active_labels,
            "forward_return_long_pct": long_return,
            "forward_return_short_pct": short_return,
        }
        joined.append(out_row)
        for key in active_labels:
            grouped[key].append(out_row)

    if len(joined) < max(1, int(min_forward_rows)):
        return {
            "artifact_type": ARTIFACT_TYPE,
            "ok": False,
            "reason": "insufficient_forward_rows",
            "research_only": True,
            "not_strategy_config": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
            "not_profitability_evidence": True,
            "label_artifact_hash": str(label_artifact.get("artifact_hash") or ""),
            "dataset_hash": str(label_artifact.get("dataset_hash") or ""),
            "joined_rows": len(joined),
            "rows": joined,
        }

    baseline = _summary(joined, min_count=min_label_count)
    label_summaries = {
        key: _summary(rows, min_count=min_label_count, baseline=baseline)
        for key, rows in sorted(grouped.items())
    }
    payload_for_hash = {
        "label_artifact_hash": str(label_artifact.get("artifact_hash") or ""),
        "dataset_hash": str(label_artifact.get("dataset_hash") or ""),
        "horizon_bars": horizon,
        "fee_bps": fee,
        "slippage_bps": slippage,
        "baseline": baseline,
        "label_summaries": label_summaries,
        "rows": joined,
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
        "venue": str(label_artifact.get("venue") or ""),
        "symbol": str(label_artifact.get("symbol") or ""),
        "timeframe": str(label_artifact.get("timeframe") or ""),
        "source": str(label_artifact.get("source") or ""),
        "dataset_hash": str(label_artifact.get("dataset_hash") or ""),
        "label_artifact_hash": str(label_artifact.get("artifact_hash") or ""),
        "artifact_hash": _sha(payload_for_hash),
        "horizon_bars": horizon,
        "fee_bps": fee,
        "slippage_bps": slippage,
        "joined_rows": len(joined),
        "label_summary_count": len(label_summaries),
        "baseline": baseline,
        "label_summaries": label_summaries,
        "rows": joined,
        "limitations": [
            "descriptive_label_conditioned_forward_returns",
            "not_strategy_signals",
            "does_not_select_or_rank_strategies",
            "requires_out_of_sample_review_before_strategy_use",
        ],
    }


def run_price_action_forward_return_join(
    *,
    label_artifact_path: str | Path,
    horizon_bars: int = 1,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    min_label_count: int = 5,
    min_forward_rows: int = 1,
) -> dict[str, Any]:
    return build_price_action_forward_return_join(
        label_artifact=load_label_artifact(label_artifact_path),
        horizon_bars=horizon_bars,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        min_label_count=min_label_count,
        min_forward_rows=min_forward_rows,
    )
