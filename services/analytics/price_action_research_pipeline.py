from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.price_action_context_labels import run_archive_price_action_context_labels
from services.analytics.price_action_forward_return_join import build_price_action_forward_return_join
from services.analytics.price_action_stability_report import build_price_action_stability_report


ARTIFACT_TYPE = "price_action_research_pipeline_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_price_action_research_pipeline(
    *,
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
    db_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    swing_lookback: int = 5,
    range_lookback: int = 10,
    opening_range_bars: int = 3,
    horizon_bars: int = 1,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    forward_min_label_count: int = 5,
    min_forward_rows: int = 1,
    window_size_rows: int = 100,
    stability_min_windows: int = 3,
    stability_min_label_count: int = 5,
    consistency_threshold: float = 0.6,
) -> dict[str, Any]:
    labels = run_archive_price_action_context_labels(
        venue=venue,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        since_ms=since_ms,
        db_path=db_path,
        swing_lookback=swing_lookback,
        range_lookback=range_lookback,
        opening_range_bars=opening_range_bars,
    )
    forward = build_price_action_forward_return_join(
        label_artifact=labels,
        horizon_bars=horizon_bars,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        min_label_count=forward_min_label_count,
        min_forward_rows=min_forward_rows,
    )
    stability = build_price_action_stability_report(
        forward_return_artifact=forward,
        window_size_rows=window_size_rows,
        min_windows=stability_min_windows,
        min_label_count=stability_min_label_count,
        consistency_threshold=consistency_threshold,
    )

    artifact_paths: dict[str, str] = {}
    if output_dir is not None:
        root = Path(output_dir)
        artifacts = {
            "labels": root / "price_action_labels.json",
            "forward_returns": root / "price_action_forward_returns.json",
            "stability": root / "price_action_stability.json",
        }
        _write_json(artifacts["labels"], labels)
        _write_json(artifacts["forward_returns"], forward)
        _write_json(artifacts["stability"], stability)
        artifact_paths = {key: str(path) for key, path in artifacts.items()}

    component_hashes = {
        "labels": str(labels.get("artifact_hash") or ""),
        "forward_returns": str(forward.get("artifact_hash") or ""),
        "stability": str(stability.get("artifact_hash") or ""),
    }
    payload_for_hash = {
        "venue": venue,
        "symbol": symbol,
        "timeframe": timeframe,
        "limit": int(limit),
        "since_ms": since_ms,
        "component_hashes": component_hashes,
        "label_ok": bool(labels.get("ok")),
        "forward_ok": bool(forward.get("ok")),
        "stability_ok": bool(stability.get("ok")),
    }
    out = {
        "artifact_type": ARTIFACT_TYPE,
        "ok": bool(labels.get("ok")) and bool(forward.get("ok")) and bool(stability.get("ok")),
        "research_only": True,
        "not_strategy_config": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_profitability_evidence": True,
        "generated_at": _utc_now(),
        "venue": str(labels.get("venue") or venue),
        "symbol": str(labels.get("symbol") or symbol),
        "timeframe": str(labels.get("timeframe") or timeframe),
        "dataset_hash": str(labels.get("dataset_hash") or ""),
        "component_hashes": component_hashes,
        "artifact_paths": artifact_paths,
        "artifact_hash": _sha(payload_for_hash),
        "stages": {
            "labels": {
                "ok": bool(labels.get("ok")),
                "reason": str(labels.get("reason") or ""),
                "row_count": int(labels.get("row_count") or 0),
                "label_count": int(len(labels.get("labels") or [])),
            },
            "forward_returns": {
                "ok": bool(forward.get("ok")),
                "reason": str(forward.get("reason") or ""),
                "joined_rows": int(forward.get("joined_rows") or 0),
                "label_summary_count": int(forward.get("label_summary_count") or 0),
            },
            "stability": {
                "ok": bool(stability.get("ok")),
                "reason": str(stability.get("reason") or ""),
                "window_count": int(stability.get("window_count") or 0),
                "stable_label_count": int(
                    sum(1 for item in dict(stability.get("label_stability") or {}).values() if item.get("stable_observation"))
                ),
            },
        },
        "limitations": [
            "research_pipeline_orchestration_only",
            "does_not_select_or_rank_strategies",
            "does_not_authorize_confirmation_filters",
            "requires_separate_review_before_strategy_use",
        ],
    }
    if output_dir is not None:
        pipeline_path = Path(output_dir) / "price_action_pipeline.json"
        _write_json(pipeline_path, out)
        out["artifact_paths"]["pipeline"] = str(pipeline_path)
        _write_json(pipeline_path, out)
    return out
