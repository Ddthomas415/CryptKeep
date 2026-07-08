from __future__ import annotations

import json
import math
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

from services.control.retirement_checker import load_all_evidence
from services.market_data.local_data_reader import (
    _load_local_ohlcv,
    load_local_ohlcv_snapshot_provenance,
)
from services.os.app_paths import data_dir

DEFAULT_TARGET_MOVE_PCT = 0.10
DEFAULT_HORIZON_BARS = 1
DEFAULT_LATE_THRESHOLD_SHARE = 0.25
DEFAULT_LOOKBACK_BARS = 5
DEFAULT_MIN_SCORED_SIGNALS = 5
DEFAULT_CANDLE_PRICE_TOLERANCE_SHARE = 0.10


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _iso_to_ms(value: Any) -> int:
    raw = str(value or "").strip()
    if not raw:
        return 0
    try:
        return int(datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp() * 1000.0)
    except Exception:
        return 0


def _ms_to_iso(ts_ms: int) -> str:
    if ts_ms <= 0:
        return ""
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).isoformat()


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(median(values))


def _action_for_signal(record: dict[str, Any]) -> str | None:
    action = str(record.get("action") or record.get("signal_action") or "").lower().strip()
    if action in {"buy", "sell"}:
        return action
    direction = str(record.get("signal_direction") or "").lower().strip()
    if direction == "long" and record.get("entry_allowed") is True:
        return "buy"
    if direction in {"short", "sell"} and record.get("entry_allowed") is True:
        return "sell"
    return None


def _is_sample_backed_signal(record: dict[str, Any]) -> bool:
    source = str(record.get("market_data_source") or "").lower().strip()
    if source == "sample_ohlcv":
        return True
    return record.get("ohlcv_sample_mode") is True


def _signal_provenance_rejection_reason(
    record: dict[str, Any],
    *,
    venue: str,
    symbol: str | None,
    timeframe: str,
) -> str:
    if _is_sample_backed_signal(record):
        return "sample_ohlcv"

    source = str(record.get("market_data_source") or "").lower().strip()
    if not source:
        return "missing_market_data_source"
    if source != "public_ohlcv":
        return "market_data_source_mismatch"
    if record.get("ohlcv_sample_mode") is not False:
        return "missing_ohlcv_sample_mode"

    expected = {
        "ohlcv_venue": str(venue or "").lower().strip(),
        "ohlcv_symbol": str(symbol or "").lower().strip(),
        "ohlcv_timeframe": str(timeframe or "").lower().strip(),
    }
    for field, expected_value in expected.items():
        if not expected_value:
            continue
        actual = str(record.get(field) or "").lower().strip()
        if not actual:
            return f"missing_{field}"
        if actual != expected_value:
            return f"{field}_mismatch"
    return ""


def _load_ohlcv_rows_from_path(path: Path) -> tuple[list[list], dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("candles") or []
    meta: dict[str, Any] = {
        "snapshot_source": "unknown" if isinstance(raw, list) else str(raw.get("source") or "unknown"),
        "snapshot_source_legacy": isinstance(raw, list),
    }
    out: list[list] = []
    for row in rows:
        if isinstance(row, list) and len(row) >= 5:
            out.append(row)
    return out, meta


def load_ohlcv_for_signal_quality(
    *,
    ohlcv_path: str | Path | None = None,
    venue: str = "coinbase",
    symbol: str | None = None,
    timeframe: str = "1d",
    limit: int = 5000,
) -> tuple[list[list], dict[str, Any]]:
    if ohlcv_path:
        path = Path(ohlcv_path).expanduser().resolve()
        if not path.exists():
            return [], {"type": "explicit_file", "path": str(path), "exists": False}
        rows, source_meta = _load_ohlcv_rows_from_path(path)
        return rows, {
            "type": "explicit_file",
            "path": str(path),
            "exists": True,
            **source_meta,
        }
    if not symbol:
        return [], {
            "type": "unavailable",
            "reason": "symbol_required_without_ohlcv_path",
            "venue": venue,
            "timeframe": timeframe,
        }
    rows = _load_local_ohlcv(venue, symbol, timeframe=timeframe, limit=limit)
    snapshot_meta = load_local_ohlcv_snapshot_provenance(venue, symbol, timeframe=timeframe)
    return rows, {
        "type": "local_snapshot",
        "path": str((data_dir() / "snapshots").resolve()),
        "exists": bool(rows),
        "venue": venue,
        "symbol": symbol,
        "timeframe": timeframe,
        "snapshot_source": str(snapshot_meta.get("source") or "unknown"),
        "snapshot_source_legacy": bool(snapshot_meta.get("legacy")),
    }


def _median_interval_ms(ohlcv: list[list]) -> int:
    if len(ohlcv) < 2:
        return 0
    deltas = []
    for i in range(1, len(ohlcv)):
        delta = _safe_int(ohlcv[i][0]) - _safe_int(ohlcv[i - 1][0])
        if delta > 0:
            deltas.append(delta)
    return int(median(deltas)) if deltas else 0


def _price_match_index(price: float, ohlcv: list[list]) -> int | None:
    if price <= 0 or not ohlcv:
        return None
    best_idx: int | None = None
    best_gap: float | None = None
    for idx, row in enumerate(ohlcv):
        close_price = _safe_float(row[4], 0.0)
        if close_price <= 0:
            continue
        gap = abs(close_price - price)
        if best_gap is None or gap < best_gap or (gap == best_gap and idx > (best_idx or -1)):
            best_gap = gap
            best_idx = idx
    return best_idx


def _candle_price_mismatch_share(price: float, row: list[Any], *, tolerance_share: float) -> float | None:
    if price <= 0:
        return None
    high_price = _safe_float(row[2], 0.0)
    low_price = _safe_float(row[3], 0.0)
    if high_price <= 0 or low_price <= 0:
        return None
    upper = high_price * (1.0 + tolerance_share)
    lower = low_price * (1.0 - tolerance_share)
    if lower <= price <= upper:
        return 0.0
    if price < lower:
        return (lower - price) / lower if lower > 0 else None
    return (price - upper) / upper if upper > 0 else None


def _match_signal_to_ohlcv(signal: dict[str, Any], ohlcv: list[list]) -> tuple[int | None, str]:
    if not ohlcv:
        return None, "unmatched"
    ts_ms = _iso_to_ms(signal.get("timestamp") or signal.get("ts") or signal.get("_logged_at"))
    first_ts = _safe_int(ohlcv[0][0])
    last_ts = _safe_int(ohlcv[-1][0])
    interval_ms = max(_median_interval_ms(ohlcv), 1)
    if ts_ms and (first_ts - interval_ms) <= ts_ms <= (last_ts + interval_ms):
        ts_list = [_safe_int(row[0]) for row in ohlcv]
        idx = bisect_right(ts_list, ts_ms) - 1
        if idx < 0:
            idx = 0
        return idx, "timestamp"
    idx = _price_match_index(_safe_float(signal.get("price"), 0.0), ohlcv)
    if idx is not None:
        return idx, "price_fallback"
    return None, "unmatched"


def _target_lead_bars(action: str, entry_price: float, future_rows: list[list], target_move_pct: float) -> int | None:
    if entry_price <= 0:
        return None
    for offset, row in enumerate(future_rows, start=1):
        high_price = _safe_float(row[2], 0.0)
        low_price = _safe_float(row[3], 0.0)
        if action == "buy" and high_price > 0 and ((high_price / entry_price) - 1.0) >= target_move_pct:
            return offset
        if action == "sell" and low_price > 0 and ((entry_price / low_price) - 1.0) >= target_move_pct:
            return offset
    return None


def _score_signal(
    *,
    signal: dict[str, Any],
    action: str,
    matched_index: int,
    match_method: str,
    ohlcv: list[list],
    horizon_bars: int,
    target_move_pct: float,
    late_threshold_share: float,
    lookback_bars: int,
) -> dict[str, Any]:
    matched_row = ohlcv[matched_index]
    future_rows = ohlcv[matched_index + 1: matched_index + 1 + horizon_bars]
    entry_price = _safe_float(signal.get("price"), 0.0) or _safe_float(matched_row[4], 0.0)
    price_mismatch_share = _candle_price_mismatch_share(
        entry_price,
        matched_row,
        tolerance_share=DEFAULT_CANDLE_PRICE_TOLERANCE_SHARE,
    )
    out: dict[str, Any] = {
        "timestamp": signal.get("timestamp") or signal.get("_logged_at") or "",
        "action": action,
        "entry_price": entry_price,
        "matched_bar_index": matched_index,
        "matched_bar_ts": _ms_to_iso(_safe_int(matched_row[0])),
        "match_method": match_method,
        "target_move_pct": float(target_move_pct),
        "target_horizon_bars": int(horizon_bars),
        "signal_direction": signal.get("signal_direction"),
        "entry_allowed": signal.get("entry_allowed"),
        "signal_price": _safe_float(signal.get("price"), 0.0),
    }
    if price_mismatch_share and price_mismatch_share > 0.0:
        out.update(
            {
                "scored": False,
                "classification": "unscored",
                "reason": "price_ohlcv_mismatch",
                "price_mismatch_share": float(price_mismatch_share),
            }
        )
        return out
    if len(future_rows) < int(horizon_bars):
        out.update(
            {
                "scored": False,
                "classification": "unscored",
                "reason": "insufficient_forward_ohlcv",
            }
        )
        return out

    highs = [_safe_float(row[2], 0.0) for row in future_rows]
    lows = [_safe_float(row[3], 0.0) for row in future_rows]
    future_close = _safe_float(future_rows[-1][4], 0.0)
    peak_idx = 0
    trough_idx = 0
    if action == "buy":
        peak_idx = max(range(len(highs)), key=lambda idx: highs[idx])
        trough_idx = min(range(len(lows)), key=lambda idx: lows[idx])
        mfe_pct = ((highs[peak_idx] / entry_price) - 1.0) if entry_price > 0 and highs[peak_idx] > 0 else 0.0
        mae_pct = ((lows[trough_idx] / entry_price) - 1.0) if entry_price > 0 and lows[trough_idx] > 0 else 0.0
        forward_return_pct = ((future_close / entry_price) - 1.0) if entry_price > 0 and future_close > 0 else 0.0
        lookback_rows = ohlcv[max(0, matched_index - lookback_bars): matched_index + 1]
        lookback_low = min((_safe_float(row[3], entry_price) for row in lookback_rows), default=entry_price)
        total_move_pct = ((highs[peak_idx] / lookback_low) - 1.0) if lookback_low > 0 and highs[peak_idx] > 0 else 0.0
        pre_signal_move_pct = ((entry_price / lookback_low) - 1.0) if lookback_low > 0 and entry_price > 0 else 0.0
    else:
        peak_idx = min(range(len(lows)), key=lambda idx: lows[idx])
        trough_idx = max(range(len(highs)), key=lambda idx: highs[idx])
        mfe_pct = ((entry_price / lows[peak_idx]) - 1.0) if entry_price > 0 and lows[peak_idx] > 0 else 0.0
        mae_pct = ((entry_price / highs[trough_idx]) - 1.0) if entry_price > 0 and highs[trough_idx] > 0 else 0.0
        forward_return_pct = ((entry_price / future_close) - 1.0) if entry_price > 0 and future_close > 0 else 0.0
        lookback_rows = ohlcv[max(0, matched_index - lookback_bars): matched_index + 1]
        lookback_high = max((_safe_float(row[2], entry_price) for row in lookback_rows), default=entry_price)
        total_move_pct = ((lookback_high / lows[peak_idx]) - 1.0) if lookback_high > 0 and lows[peak_idx] > 0 else 0.0
        pre_signal_move_pct = ((lookback_high / entry_price) - 1.0) if lookback_high > 0 and entry_price > 0 else 0.0

    raw_late_share = (pre_signal_move_pct / total_move_pct) if total_move_pct > 0 else 0.0
    target_hit = mfe_pct >= target_move_pct
    late_share = raw_late_share if target_hit else None
    late_hit = target_hit and raw_late_share > late_threshold_share
    capture_ratio = 0.0
    if mfe_pct > 0:
        capture_ratio = max(forward_return_pct, 0.0) / mfe_pct
    lead_bars = _target_lead_bars(action, entry_price, future_rows, target_move_pct)
    peak_bar = future_rows[peak_idx]

    out.update(
        {
            "scored": True,
            "classification": "late_hit" if late_hit else "hit" if target_hit else "false_positive",
            "late_hit": bool(late_hit),
            "hit": bool(target_hit),
            "lead_bars": lead_bars,
            "forward_return_pct": float(forward_return_pct),
            "mfe_pct": float(mfe_pct),
            "mae_pct": float(mae_pct),
            "capture_ratio": float(capture_ratio),
            "pre_signal_move_share": float(late_share) if late_share is not None else None,
            "peak_bar_ts": _ms_to_iso(_safe_int(peak_bar[0])),
            "target_peak_price": float(highs[peak_idx] if action == "buy" else lows[peak_idx]),
        }
    )
    return out


def _dedupe_signals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int]] = set()
    deduped: list[dict[str, Any]] = []
    ordered = sorted(
        rows,
        key=lambda row: (
            row["matched_bar_index"],
            row["action"],
            _iso_to_ms(row["timestamp"]),
            _iso_to_ms(row.get("_logged_at")),
        ),
    )
    for row in ordered:
        key = (str(row["action"]), int(row["matched_bar_index"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _interpret_summary(summary: dict[str, Any]) -> str:
    scored = int(summary.get("signals_scored") or 0)
    hit_rate = _safe_float(summary.get("hit_rate"), 0.0)
    late_hit_rate = _safe_float(summary.get("late_hit_rate"), 0.0)
    false_positive_rate = _safe_float(summary.get("false_positive_rate"), 0.0)
    avg_capture_ratio = _safe_float(summary.get("avg_capture_ratio"), 0.0)
    if scored < DEFAULT_MIN_SCORED_SIGNALS:
        return "insufficient_sample"
    if hit_rate >= 0.50 and avg_capture_ratio >= 0.35 and late_hit_rate <= 0.25:
        return "early_edge_present"
    if hit_rate >= 0.50 and late_hit_rate > 0.25:
        return "directionally_right_but_late"
    if false_positive_rate >= 0.60:
        return "noisy_false_positive_prone"
    return "mixed_signal_quality"


def build_signal_quality_report(
    *,
    strategy_id: str,
    target_move_pct: float = DEFAULT_TARGET_MOVE_PCT,
    horizon_bars: int = DEFAULT_HORIZON_BARS,
    late_threshold_share: float = DEFAULT_LATE_THRESHOLD_SHARE,
    lookback_bars: int = DEFAULT_LOOKBACK_BARS,
    evidence_dir: str | Path | None = None,
    ohlcv_path: str | Path | None = None,
    ohlcv_rows: list[list] | None = None,
    venue: str = "coinbase",
    symbol: str | None = None,
    timeframe: str = "1d",
    require_matching_provenance: bool = True,
) -> dict[str, Any]:
    ev_dir = Path(evidence_dir).expanduser().resolve() if evidence_dir else (data_dir() / "evidence" / strategy_id).resolve()
    evidence = load_all_evidence(ev_dir)
    signals = evidence.get("signal") or []
    loaded_ohlcv = ohlcv_rows
    ohlcv_source: dict[str, Any]
    if loaded_ohlcv is None:
        loaded_ohlcv, ohlcv_source = load_ohlcv_for_signal_quality(
            ohlcv_path=ohlcv_path,
            venue=venue,
            symbol=symbol,
            timeframe=timeframe,
        )
    else:
        ohlcv_source = {"type": "in_memory_rows", "rows": len(loaded_ohlcv)}

    report: dict[str, Any] = {
        "ok": bool(loaded_ohlcv),
        "strategy_id": strategy_id,
        "symbol": symbol,
        "venue": venue,
        "timeframe": timeframe,
        "target_move_pct": float(target_move_pct),
        "horizon_bars": int(horizon_bars),
        "late_threshold_share": float(late_threshold_share),
        "lookback_bars": int(lookback_bars),
        "evidence_dir": str(ev_dir),
        "signal_records_total": len(signals),
        "provenance_policy": {
            "required": bool(require_matching_provenance),
            "expected": {
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_venue": str(venue or ""),
                "ohlcv_symbol": str(symbol or ""),
                "ohlcv_timeframe": str(timeframe or ""),
            },
            "rule": (
                "Only matching non-sample public OHLCV signal evidence is scored."
                if require_matching_provenance
                else "Unqualified non-sample signal evidence is allowed for explicit research use."
            ),
        },
        "ohlcv_source": ohlcv_source,
        "rows": [],
        "summary": {},
    }
    eligible_signals: list[dict[str, Any]] = []
    matching_provenance_signals = 0
    excluded_sample_signals = 0
    excluded_unqualified_signals = 0
    excluded_reason_counts: Counter[str] = Counter()
    unqualified_reason_counts: Counter[str] = Counter()
    for signal in signals:
        rejection_reason = _signal_provenance_rejection_reason(
            signal,
            venue=venue,
            symbol=symbol,
            timeframe=timeframe,
        )
        if rejection_reason == "sample_ohlcv":
            excluded_sample_signals += 1
            excluded_reason_counts[rejection_reason] += 1
            continue
        if not rejection_reason:
            matching_provenance_signals += 1
        else:
            unqualified_reason_counts[rejection_reason] += 1
        if require_matching_provenance and rejection_reason:
            excluded_unqualified_signals += 1
            excluded_reason_counts[rejection_reason] += 1
            continue
        eligible_signals.append(signal)

    if not loaded_ohlcv:
        report["reason"] = "no_ohlcv"
        report["summary"] = {
            "signals_total": len(signals),
            "matching_provenance_signal_records": matching_provenance_signals,
            "unqualified_signal_records": sum(unqualified_reason_counts.values()),
            "unqualified_signal_reason_counts": dict(unqualified_reason_counts),
            "eligible_signal_records": len(eligible_signals),
            "excluded_sample_signals": excluded_sample_signals,
            "excluded_unqualified_signals": excluded_unqualified_signals,
            "excluded_signal_reason_counts": dict(excluded_reason_counts),
            "actionable_signals": 0,
            "deduped_signals": 0,
            "signals_scored": 0,
            "unscored_signals": 0,
            "target_move_hits": 0,
            "late_hits": 0,
            "false_positives": 0,
            "match_methods": {},
            "interpretation": "insufficient_sample",
        }
        return report

    actionable_rows: list[dict[str, Any]] = []
    for signal in eligible_signals:
        action = _action_for_signal(signal)
        if not action:
            continue
        matched_index, match_method = _match_signal_to_ohlcv(signal, loaded_ohlcv)
        if matched_index is None:
            continue
        actionable_rows.append(
            {
                **signal,
                "action": action,
                "matched_bar_index": matched_index,
                "match_method": match_method,
                "timestamp": signal.get("timestamp") or signal.get("_logged_at") or "",
            }
        )

    deduped = _dedupe_signals(actionable_rows)
    scored_rows = [
        _score_signal(
            signal=row,
            action=str(row["action"]),
            matched_index=int(row["matched_bar_index"]),
            match_method=str(row["match_method"]),
            ohlcv=loaded_ohlcv,
            horizon_bars=int(horizon_bars),
            target_move_pct=float(target_move_pct),
            late_threshold_share=float(late_threshold_share),
            lookback_bars=int(lookback_bars),
        )
        for row in deduped
    ]
    report["rows"] = scored_rows

    scored_only = [row for row in scored_rows if row.get("scored") is True]
    hits = [row for row in scored_only if row.get("classification") in {"hit", "late_hit"}]
    late_hits = [row for row in scored_only if row.get("classification") == "late_hit"]
    false_positives = [row for row in scored_only if row.get("classification") == "false_positive"]
    lead_bars = [int(row["lead_bars"]) for row in hits if row.get("lead_bars") is not None]
    capture_ratios = [float(row["capture_ratio"]) for row in scored_only]
    mfes = [float(row["mfe_pct"]) for row in scored_only]
    maes = [float(row["mae_pct"]) for row in scored_only]
    match_methods = Counter(str(row.get("match_method") or "") for row in deduped)

    summary = {
        "signals_total": len(signals),
        "matching_provenance_signal_records": matching_provenance_signals,
        "unqualified_signal_records": sum(unqualified_reason_counts.values()),
        "unqualified_signal_reason_counts": dict(unqualified_reason_counts),
        "eligible_signal_records": len(eligible_signals),
        "excluded_sample_signals": excluded_sample_signals,
        "excluded_unqualified_signals": excluded_unqualified_signals,
        "excluded_signal_reason_counts": dict(excluded_reason_counts),
        "actionable_signals": len(actionable_rows),
        "deduped_signals": len(deduped),
        "signals_scored": len(scored_only),
        "unscored_signals": len(scored_rows) - len(scored_only),
        "price_mismatch_signals": sum(1 for row in scored_rows if row.get("reason") == "price_ohlcv_mismatch"),
        "target_move_hits": len(hits),
        "late_hits": len(late_hits),
        "false_positives": len(false_positives),
        "hit_rate": (len(hits) / len(scored_only)) if scored_only else 0.0,
        "late_hit_rate": (len(late_hits) / len(scored_only)) if scored_only else 0.0,
        "false_positive_rate": (len(false_positives) / len(scored_only)) if scored_only else 0.0,
        "avg_lead_bars": _mean([float(v) for v in lead_bars]),
        "median_lead_bars": _median([float(v) for v in lead_bars]),
        "avg_capture_ratio": _mean(capture_ratios),
        "median_capture_ratio": _median(capture_ratios),
        "avg_mfe_pct": _mean(mfes),
        "avg_mae_pct": _mean(maes),
        "match_methods": dict(match_methods),
    }
    summary["interpretation"] = _interpret_summary(summary)
    report["summary"] = summary
    report["ok"] = True
    return report


def write_signal_quality_artifacts(report: dict[str, Any]) -> dict[str, str]:
    root = (data_dir() / "signal_quality").resolve()
    root.mkdir(parents=True, exist_ok=True)
    strategy_id = str(report.get("strategy_id") or "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_path = (root / "signal_quality.latest.json").resolve()
    history_path = (root / f"signal_quality_{strategy_id}_{ts}.json").resolve()
    payload = json.dumps(report, indent=2, sort_keys=True)
    latest_path.write_text(payload, encoding="utf-8")
    history_path.write_text(payload, encoding="utf-8")
    return {"latest_path": str(latest_path), "history_path": str(history_path)}
