from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any

from services.backtest.price_action_context import (
    ARTIFACT_TYPE as LABEL_ARTIFACT_TYPE,
    LIMITATION_FLAGS,
    run_archive_price_action_context,
)
from services.execution.fill_model import apply_fee_slippage
from services.market_data.symbol_router import normalize_symbol, normalize_venue


ARTIFACT_TYPE = "price_action_forward_returns_v1"


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _f(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


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
    direction = str(side or "").lower().strip()
    if direction == "long":
        entry = apply_fee_slippage(
            mid_px=entry_px,
            side="buy",
            qty=1.0,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )
        exit_fill = apply_fee_slippage(
            mid_px=exit_px,
            side="sell",
            qty=1.0,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )
        basis = entry.notional + entry.fee
        profit = (exit_fill.notional - exit_fill.fee) - basis
    elif direction == "short":
        entry = apply_fee_slippage(
            mid_px=entry_px,
            side="sell",
            qty=1.0,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )
        exit_fill = apply_fee_slippage(
            mid_px=exit_px,
            side="buy",
            qty=1.0,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )
        basis = entry.notional + entry.fee
        profit = (entry.notional - entry.fee) - (exit_fill.notional + exit_fill.fee)
    else:
        return None
    if basis <= 0.0:
        return None
    return float((profit / basis) * 100.0)


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _summary(values: list[float]) -> dict[str, Any]:
    wins = [value for value in values if value > 0.0]
    return {
        "sample_size": int(len(values)),
        "positive_count": int(len(wins)),
        "positive_ratio": None if not values else float(len(wins) / len(values)),
        "avg_net_forward_return_pct": _avg(values),
        "min_net_forward_return_pct": None if not values else float(min(values)),
        "max_net_forward_return_pct": None if not values else float(max(values)),
    }


def _active_label_pairs(labels: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name, value in sorted(dict(labels or {}).items()):
        if value is None or value is False or value == "":
            continue
        suffix = "true" if value is True else str(value).strip().lower()
        out.append((str(name), suffix))
    return out


def _label_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    long_by_label: dict[str, list[float]] = defaultdict(list)
    short_by_label: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        long_ret = row.get("long_net_forward_return_pct")
        short_ret = row.get("short_net_forward_return_pct")
        if long_ret is None or short_ret is None:
            continue
        for label in list(row.get("active_labels") or []):
            key = str(label)
            long_by_label[key].append(float(long_ret))
            short_by_label[key].append(float(short_ret))

    labels = sorted(set(long_by_label) | set(short_by_label))
    return {
        label: {
            "label": label,
            "long": _summary(long_by_label.get(label, [])),
            "short": _summary(short_by_label.get(label, [])),
        }
        for label in labels
    }


def build_price_action_forward_return_report(
    *,
    label_artifact: dict[str, Any],
    venue: str,
    symbol: str,
    timeframe: str,
    horizon_bars: int = 1,
    min_labeled_rows: int = 1,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    """Build a forward-return report from an already computed label artifact."""
    horizon = max(1, int(horizon_bars))
    labels = list(label_artifact.get("labels") or [])
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(labels):
        exit_idx = idx + horizon
        if exit_idx >= len(labels):
            continue
        exit_row = labels[exit_idx]
        entry_px = _f(row.get("close"))
        exit_px = _f(exit_row.get("close"))
        label_pairs = _active_label_pairs(dict(row.get("labels") or {}))
        active_labels = [f"{name}:{value}" for name, value in label_pairs]
        long_return = _round_trip_return_pct(
            side="long",
            entry_px=entry_px,
            exit_px=exit_px,
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        short_return = _round_trip_return_pct(
            side="short",
            entry_px=entry_px,
            exit_px=exit_px,
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        rows.append(
            {
                "ts_ms": int(row.get("ts_ms") or 0),
                "exit_ts_ms": int(exit_row.get("ts_ms") or 0),
                "entry_close": float(entry_px),
                "exit_close": float(exit_px),
                "horizon_bars": int(horizon),
                "active_labels": active_labels,
                "long_net_forward_return_pct": (
                    None if long_return is None else round(float(long_return), 8)
                ),
                "short_net_forward_return_pct": (
                    None if short_return is None else round(float(short_return), 8)
                ),
            }
        )

    labeled_rows = [row for row in rows if list(row.get("active_labels") or [])]
    label_summaries = _label_summary(labeled_rows)
    long_all = [
        float(row["long_net_forward_return_pct"])
        for row in rows
        if row.get("long_net_forward_return_pct") is not None
    ]
    short_all = [
        float(row["short_net_forward_return_pct"])
        for row in rows
        if row.get("short_net_forward_return_pct") is not None
    ]
    dataset_hash = _sha(
        {
            "artifact_type": ARTIFACT_TYPE,
            "label_dataset_hash": (
                (label_artifact.get("dataset") or {}).get("dataset_hash")
            ),
            "horizon_bars": int(horizon),
            "fee_bps": float(fee_bps),
            "slippage_bps": float(slippage_bps),
            "label_config": dict(label_artifact.get("label_config") or {}),
            "rows": rows,
        }
    )
    ok = len(labeled_rows) >= max(1, int(min_labeled_rows))
    return {
        "ok": bool(ok),
        "reason": "ok" if ok else "insufficient_labeled_rows",
        "artifact_type": ARTIFACT_TYPE,
        **LIMITATION_FLAGS,
        "limitation_flags": dict(LIMITATION_FLAGS),
        "venue": normalize_venue(venue),
        "symbol": normalize_symbol(symbol),
        "timeframe": str(timeframe),
        "horizon_bars": int(horizon),
        "fee_bps": float(fee_bps),
        "slippage_bps": float(slippage_bps),
        "label_artifact_type": LABEL_ARTIFACT_TYPE,
        "dataset": dict(label_artifact.get("dataset") or {}),
        "dataset_hash": dataset_hash,
        "source_label_counts": dict(label_artifact.get("label_counts") or {}),
        "label_config": dict(label_artifact.get("label_config") or {}),
        "row_count": int(len(rows)),
        "labeled_row_count": int(len(labeled_rows)),
        "summary": {
            "unconditioned_long": _summary(long_all),
            "unconditioned_short": _summary(short_all),
            "label_bucket_count": int(len(label_summaries)),
        },
        "label_summaries": label_summaries,
        "rows": rows,
        "limitations": [
            "research_only",
            "forward_return_only",
            "unit_size_no_position_state",
            "no_portfolio_pnl",
            "not_strategy_config",
            "not_campaign_evidence",
            "not_promotion_evidence",
            "not_profitability_evidence",
        ],
    }


def run_price_action_forward_returns(
    *,
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
    db_path: str | None = None,
    horizon_bars: int = 1,
    min_labeled_rows: int = 1,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    label_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Research-only label-conditioned forward-return report.

    This evaluates unit-size long/short forward returns after modeled
    fee/slippage. It does not simulate portfolio state, choose trades, alter
    strategy config, or provide promotion evidence.
    """
    horizon = max(1, int(horizon_bars))
    loaded = run_archive_price_action_context(
        venue=str(venue),
        symbol=str(symbol),
        timeframe=str(timeframe),
        limit=int(limit),
        since_ms=since_ms,
        db_path=db_path,
        label_config=label_config,
    )
    if not bool(loaded.get("ok")):
        return {
            "ok": False,
            "reason": str(loaded.get("reason") or "label_archive_unavailable"),
            "artifact_type": ARTIFACT_TYPE,
            **LIMITATION_FLAGS,
            "limitation_flags": dict(LIMITATION_FLAGS),
            "venue": normalize_venue(venue),
            "symbol": normalize_symbol(symbol),
            "timeframe": str(timeframe),
            "horizon_bars": int(horizon),
            "fee_bps": float(fee_bps),
            "slippage_bps": float(slippage_bps),
            "label_artifact_type": LABEL_ARTIFACT_TYPE,
            "dataset": dict(loaded.get("dataset") or {}),
            "rows": [],
            "label_summaries": {},
        }

    return build_price_action_forward_return_report(
        label_artifact=loaded,
        venue=venue,
        symbol=symbol,
        timeframe=timeframe,
        horizon_bars=horizon,
        min_labeled_rows=min_labeled_rows,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
    )
