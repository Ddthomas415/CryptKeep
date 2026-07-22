from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.funding_context_price_join import run_funding_context_price_join
from services.analytics.funding_context_replay import run_funding_context_replay
from services.analytics.funding_threshold_sensitivity import run_funding_threshold_sensitivity


ARTIFACT_TYPE = "crypto_edge_research_pipeline_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_crypto_edge_research_pipeline(
    *,
    edge_db_path: str | Path | None = None,
    archive_db_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    context_source: str = "live_public",
    context_venue: str = "okx",
    context_symbol: str = "BTC/USDT:USDT",
    price_venue: str = "okx",
    price_symbol: str = "BTC/USDT",
    timeframe: str = "5m",
    funding_limit: int = 500,
    ohlcv_limit: int = 500,
    horizon_bars: int = 1,
    min_rows: int = 1,
    min_joined_rows: int = 1,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    long_thresholds_pct: list[float] | tuple[float, ...] = (0.005, 0.01, 0.02, 0.05),
    short_thresholds_pct: list[float] | tuple[float, ...] = (-0.005, -0.01, -0.02, -0.05),
) -> dict[str, Any]:
    replay = run_funding_context_replay(
        db_path=edge_db_path,
        source=context_source,
        venue=context_venue,
        symbol=context_symbol,
        limit=funding_limit,
        min_rows=min_rows,
    )
    price_join = run_funding_context_price_join(
        edge_db_path=edge_db_path,
        archive_db_path=archive_db_path,
        context_source=context_source,
        context_venue=context_venue,
        context_symbol=context_symbol,
        price_venue=price_venue,
        price_symbol=price_symbol,
        timeframe=timeframe,
        funding_limit=funding_limit,
        ohlcv_limit=ohlcv_limit,
        horizon_bars=horizon_bars,
        min_joined_rows=min_joined_rows,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
    )

    artifact_paths: dict[str, str] = {}
    price_join_path: Path | None = None
    if output_dir is not None:
        root = Path(output_dir)
        replay_path = root / "funding_context_replay.json"
        price_join_path = root / "funding_context_price_join.json"
        _write_json(replay_path, replay)
        _write_json(price_join_path, price_join)
        artifact_paths["replay"] = str(replay_path)
        artifact_paths["price_join"] = str(price_join_path)
    else:
        root = Path("/tmp")
        price_join_path = root / f"cbp-funding-context-price-join-{_sha(price_join)[:12]}.json"
        _write_json(price_join_path, price_join)

    sensitivity = run_funding_threshold_sensitivity(
        input_path=price_join_path,
        long_thresholds_pct=long_thresholds_pct,
        short_thresholds_pct=short_thresholds_pct,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
    )
    if output_dir is not None:
        sensitivity_path = Path(output_dir) / "funding_threshold_sensitivity.json"
        _write_json(sensitivity_path, sensitivity)
        artifact_paths["threshold_sensitivity"] = str(sensitivity_path)
    elif price_join_path is not None:
        try:
            price_join_path.unlink(missing_ok=True)
        except Exception:
            pass

    component_hashes = {
        "replay": str(replay.get("dataset_hash") or ""),
        "price_join": str(price_join.get("dataset_hash") or ""),
        "threshold_sensitivity": str(sensitivity.get("dataset_hash") or ""),
    }
    payload_for_hash = {
        "component_hashes": component_hashes,
        "context_source": context_source,
        "context_venue": context_venue,
        "context_symbol": context_symbol,
        "price_venue": price_venue,
        "price_symbol": price_symbol,
        "timeframe": timeframe,
        "fee_bps": float(fee_bps),
        "slippage_bps": float(slippage_bps),
        "replay_ok": bool(replay.get("ok")),
        "price_join_ok": bool(price_join.get("ok")),
        "threshold_sensitivity_ok": bool(sensitivity.get("ok")),
    }
    out = {
        "artifact_type": ARTIFACT_TYPE,
        "ok": bool(replay.get("ok")) and bool(price_join.get("ok")) and bool(sensitivity.get("ok")),
        "research_only": True,
        "not_strategy_config": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_profitability_evidence": True,
        "generated_at": _utc_now(),
        "strategy": "funding_extreme",
        "context_source": str(context_source),
        "context_venue": str(context_venue),
        "context_symbol": str(context_symbol),
        "price_venue": str(price_venue),
        "price_symbol": str(price_symbol),
        "timeframe": str(timeframe),
        "fee_bps": float(fee_bps),
        "slippage_bps": float(slippage_bps),
        "component_hashes": component_hashes,
        "artifact_paths": artifact_paths,
        "artifact_hash": _sha(payload_for_hash),
        "stages": {
            "replay": {
                "ok": bool(replay.get("ok")),
                "reason": str(replay.get("reason") or ""),
                "row_count": int(replay.get("row_count") or 0),
                "action_counts": dict(replay.get("action_counts") or {}),
            },
            "price_join": {
                "ok": bool(price_join.get("ok")),
                "reason": str(price_join.get("reason") or ""),
                "joined_rows": int(price_join.get("joined_rows") or 0),
                "action_counts": dict(price_join.get("action_counts") or {}),
            },
            "threshold_sensitivity": {
                "ok": bool(sensitivity.get("ok")),
                "reason": str(sensitivity.get("reason") or ""),
                "grid_count": int(len(sensitivity.get("grid_rows") or [])),
                "max_actionable_rows": int(((sensitivity.get("summary") or {}).get("max_actionable_rows")) or 0),
            },
        },
        "limitations": [
            "research_pipeline_orchestration_only",
            "forward_return_only",
            "unit_size_no_position_state",
            "does_not_change_strategy_config",
            "does_not_start_campaigns",
            "not_promotion_evidence",
        ],
    }
    if output_dir is not None:
        pipeline_path = Path(output_dir) / "crypto_edge_research_pipeline.json"
        _write_json(pipeline_path, out)
        out["artifact_paths"]["pipeline"] = str(pipeline_path)
        _write_json(pipeline_path, out)
    return out
