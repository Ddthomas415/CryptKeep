from __future__ import annotations

import hashlib
import json
from typing import Any

from services.analytics.price_action_forward_returns import (
    build_price_action_forward_return_report,
)
from services.backtest.ohlcv_archive import (
    ARCHIVE_SOURCE,
    load_archived_ohlcv,
    normalize_ohlcv_rows,
    ohlcv_dataset_hash,
)
from services.backtest.price_action_context import (
    LIMITATION_FLAGS,
    build_price_action_context_artifact,
)
from services.market_data.symbol_router import normalize_symbol, normalize_venue


ARTIFACT_TYPE = "price_action_window_stability_v1"


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _delta(value: Any, baseline: Any) -> float | None:
    try:
        left = float(value)
        right = float(baseline)
    except Exception:
        return None
    return float(left - right)


def _window_ranges(row_count: int, *, window_bars: int, step_bars: int) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    if row_count < window_bars:
        return windows
    start = 0
    while start + window_bars <= row_count:
        windows.append((start, start + window_bars))
        start += step_bars
    return windows


def _window_label_deltas(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    baseline = dict(report.get("summary") or {})
    long_base = ((baseline.get("unconditioned_long") or {}).get("avg_net_forward_return_pct"))
    short_base = ((baseline.get("unconditioned_short") or {}).get("avg_net_forward_return_pct"))
    out: dict[str, dict[str, Any]] = {}
    for label, summary in sorted(dict(report.get("label_summaries") or {}).items()):
        long_summary = dict((summary or {}).get("long") or {})
        short_summary = dict((summary or {}).get("short") or {})
        long_delta = _delta(long_summary.get("avg_net_forward_return_pct"), long_base)
        short_delta = _delta(short_summary.get("avg_net_forward_return_pct"), short_base)
        out[str(label)] = {
            "label": str(label),
            "long_sample_size": int(long_summary.get("sample_size") or 0),
            "short_sample_size": int(short_summary.get("sample_size") or 0),
            "long_avg_delta_vs_unconditioned_pct": long_delta,
            "short_avg_delta_vs_unconditioned_pct": short_delta,
            "long_outperformed_unconditioned": None if long_delta is None else bool(long_delta > 0.0),
            "short_outperformed_unconditioned": None if short_delta is None else bool(short_delta > 0.0),
        }
    return out


def _label_stability(windows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for window in windows:
        for label, row in dict(window.get("label_deltas") or {}).items():
            bucket = grouped.setdefault(
                str(label),
                {
                    "label": str(label),
                    "window_count": 0,
                    "long_sample_size": 0,
                    "short_sample_size": 0,
                    "long_deltas": [],
                    "short_deltas": [],
                    "long_outperform_windows": 0,
                    "short_outperform_windows": 0,
                },
            )
            bucket["window_count"] += 1
            bucket["long_sample_size"] += int(row.get("long_sample_size") or 0)
            bucket["short_sample_size"] += int(row.get("short_sample_size") or 0)
            long_delta = row.get("long_avg_delta_vs_unconditioned_pct")
            short_delta = row.get("short_avg_delta_vs_unconditioned_pct")
            if long_delta is not None:
                bucket["long_deltas"].append(float(long_delta))
                if float(long_delta) > 0.0:
                    bucket["long_outperform_windows"] += 1
            if short_delta is not None:
                bucket["short_deltas"].append(float(short_delta))
                if float(short_delta) > 0.0:
                    bucket["short_outperform_windows"] += 1

    out: dict[str, dict[str, Any]] = {}
    for label, bucket in sorted(grouped.items()):
        window_count = int(bucket["window_count"])
        long_deltas = list(bucket["long_deltas"])
        short_deltas = list(bucket["short_deltas"])
        out[label] = {
            "label": label,
            "window_count": window_count,
            "long_sample_size": int(bucket["long_sample_size"]),
            "short_sample_size": int(bucket["short_sample_size"]),
            "avg_long_delta_vs_unconditioned_pct": _avg(long_deltas),
            "avg_short_delta_vs_unconditioned_pct": _avg(short_deltas),
            "long_outperform_window_ratio": None
            if not long_deltas
            else float(int(bucket["long_outperform_windows"]) / len(long_deltas)),
            "short_outperform_window_ratio": None
            if not short_deltas
            else float(int(bucket["short_outperform_windows"]) / len(short_deltas)),
            "long_underperform_window_ratio": None
            if not long_deltas
            else float((len(long_deltas) - int(bucket["long_outperform_windows"])) / len(long_deltas)),
            "short_underperform_window_ratio": None
            if not short_deltas
            else float((len(short_deltas) - int(bucket["short_outperform_windows"])) / len(short_deltas)),
        }
    return out


def run_price_action_window_stability(
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
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    label_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    exchange = normalize_venue(venue)
    canonical_symbol = normalize_symbol(symbol)
    loaded = load_archived_ohlcv(
        exchange,
        canonical_symbol,
        timeframe=str(timeframe),
        limit=int(limit),
        since_ms=since_ms,
        db_path=db_path,
    )
    if not bool(loaded.get("ok")):
        return {
            "ok": False,
            "reason": str(loaded.get("reason") or "archive_unavailable"),
            "artifact_type": ARTIFACT_TYPE,
            **LIMITATION_FLAGS,
            "limitation_flags": dict(LIMITATION_FLAGS),
            "venue": exchange,
            "symbol": canonical_symbol,
            "timeframe": str(timeframe),
            "windows": [],
            "label_stability": {},
        }

    rows = normalize_ohlcv_rows(list(loaded.get("rows") or []))
    window_size = max(int(horizon_bars) + 2, int(window_bars))
    step = max(1, int(step_bars if step_bars is not None else window_size))
    ranges = _window_ranges(len(rows), window_bars=window_size, step_bars=step)
    windows: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(ranges, start=1):
        window_rows = rows[start:end]
        window_dataset_hash = ohlcv_dataset_hash(
            venue=exchange,
            symbol=canonical_symbol,
            timeframe=str(timeframe),
            rows=window_rows,
            source=f"{ARCHIVE_SOURCE}:window",
        )
        label_artifact = build_price_action_context_artifact(
            rows=window_rows,
            venue=exchange,
            symbol=canonical_symbol,
            timeframe=str(timeframe),
            source=f"{ARCHIVE_SOURCE}:window",
            dataset_hash=window_dataset_hash,
            archive_path=str(loaded.get("archive_path") or ""),
            label_config=label_config,
        )
        forward_report = build_price_action_forward_return_report(
            label_artifact=label_artifact,
            venue=exchange,
            symbol=canonical_symbol,
            timeframe=str(timeframe),
            horizon_bars=int(horizon_bars),
            min_labeled_rows=int(min_labeled_rows),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        windows.append(
            {
                "window_index": int(index),
                "start_row": int(start),
                "end_row_exclusive": int(end),
                "start_ts_ms": int(window_rows[0][0]),
                "end_ts_ms": int(window_rows[-1][0]),
                "ok": bool(forward_report.get("ok")),
                "reason": str(forward_report.get("reason") or ""),
                "dataset_hash": window_dataset_hash,
                "row_count": int(len(window_rows)),
                "labeled_row_count": int(forward_report.get("labeled_row_count") or 0),
                "summary": dict(forward_report.get("summary") or {}),
                "label_deltas": _window_label_deltas(forward_report),
            }
        )

    ok_windows = [window for window in windows if bool(window.get("ok"))]
    label_stability = _label_stability(ok_windows)
    base_dataset_hash = str(
        loaded.get("dataset_hash")
        or ohlcv_dataset_hash(
            venue=exchange,
            symbol=canonical_symbol,
            timeframe=str(timeframe),
            rows=rows,
        )
    )
    artifact_hash = _sha(
        {
            "artifact_type": ARTIFACT_TYPE,
            "base_dataset_hash": base_dataset_hash,
            "window_bars": int(window_size),
            "step_bars": int(step),
            "horizon_bars": int(horizon_bars),
            "fee_bps": float(fee_bps),
            "slippage_bps": float(slippage_bps),
            "label_config": dict(label_config or {}),
            "windows": windows,
        }
    )
    enough_windows = len(ok_windows) >= max(1, int(min_windows))
    return {
        "ok": bool(enough_windows),
        "reason": "ok" if enough_windows else "insufficient_ok_windows",
        "artifact_type": ARTIFACT_TYPE,
        **LIMITATION_FLAGS,
        "limitation_flags": dict(LIMITATION_FLAGS),
        "venue": exchange,
        "symbol": canonical_symbol,
        "timeframe": str(timeframe),
        "window_bars": int(window_size),
        "step_bars": int(step),
        "min_windows": int(min_windows),
        "horizon_bars": int(horizon_bars),
        "min_labeled_rows": int(min_labeled_rows),
        "fee_bps": float(fee_bps),
        "slippage_bps": float(slippage_bps),
        "dataset": {
            "source": str(loaded.get("source") or ARCHIVE_SOURCE),
            "archive_path": loaded.get("archive_path"),
            "dataset_hash": base_dataset_hash,
            "bars": int(len(rows)),
            "start_ts_ms": int(rows[0][0]) if rows else None,
            "end_ts_ms": int(rows[-1][0]) if rows else None,
        },
        "dataset_hash": artifact_hash,
        "window_count": int(len(windows)),
        "ok_window_count": int(len(ok_windows)),
        "label_bucket_count": int(len(label_stability)),
        "label_stability": label_stability,
        "windows": windows,
        "limitations": [
            "research_only",
            "window_stability_only",
            "unit_size_no_position_state",
            "no_portfolio_pnl",
            "not_strategy_config",
            "not_campaign_evidence",
            "not_promotion_evidence",
            "not_profitability_evidence",
        ],
    }
