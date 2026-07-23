from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

from services.backtest.ohlcv_archive import normalize_ohlcv_rows, ohlcv_dataset_hash
from services.market_data.symbol_router import normalize_symbol, normalize_venue


ARTIFACT_TYPE = "price_action_context_labels_v1"
LIMITATIONS = [
    "research_only",
    "not_strategy_config",
    "not_campaign_evidence",
    "not_promotion_evidence",
    "not_profitability_evidence",
]


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out


def _safe_ts_ms(row: list[Any]) -> int | None:
    if not isinstance(row, (list, tuple)) or not row:
        return None
    try:
        ts = int(float(row[0]))
    except Exception:
        return None
    if ts <= 0:
        return None
    if ts < 10_000_000_000:
        ts *= 1000
    return ts


def _utc_day(ts_ms: int | None) -> str:
    if ts_ms is None:
        return ""
    return dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.UTC).date().isoformat()


def _range(row: list[Any]) -> float:
    return max(0.0, _fnum(row[2]) - _fnum(row[3]))


def _body(row: list[Any]) -> float:
    return abs(_fnum(row[4]) - _fnum(row[1]))


def _upper_wick(row: list[Any]) -> float:
    return max(0.0, _fnum(row[2]) - max(_fnum(row[1]), _fnum(row[4])))


def _lower_wick(row: list[Any]) -> float:
    return max(0.0, min(_fnum(row[1]), _fnum(row[4])) - _fnum(row[3]))


def _direction(row: list[Any]) -> str:
    close_px = _fnum(row[4])
    open_px = _fnum(row[1])
    if close_px > open_px:
        return "bullish"
    if close_px < open_px:
        return "bearish"
    return "neutral"


def _avg(values: list[float]) -> float:
    clean = [float(v) for v in values if v >= 0.0]
    return float(sum(clean) / len(clean)) if clean else 0.0


def _engulfing(rows: list[list[Any]], idx: int) -> str:
    if idx <= 0:
        return ""
    prev = rows[idx - 1]
    cur = rows[idx]
    prev_open = _fnum(prev[1])
    prev_close = _fnum(prev[4])
    cur_open = _fnum(cur[1])
    cur_close = _fnum(cur[4])
    prev_low = min(prev_open, prev_close)
    prev_high = max(prev_open, prev_close)
    cur_low = min(cur_open, cur_close)
    cur_high = max(cur_open, cur_close)
    if cur_low <= prev_low and cur_high >= prev_high and _body(cur) > _body(prev):
        return _direction(cur)
    return ""


def _rejection_wick(
    row: list[Any],
    *,
    body_multiple: float,
    range_fraction: float,
) -> str:
    body = max(_body(row), 1e-12)
    candle_range = max(_range(row), 1e-12)
    upper = _upper_wick(row)
    lower = _lower_wick(row)
    upper_reject = upper >= body_multiple * body and upper >= range_fraction * candle_range
    lower_reject = lower >= body_multiple * body and lower >= range_fraction * candle_range
    if upper_reject and lower_reject:
        return "both"
    if upper_reject:
        return "upper"
    if lower_reject:
        return "lower"
    return ""


def _recent_extremes(rows: list[list[Any]], start: int, end: int) -> tuple[float | None, float | None]:
    segment = rows[max(0, start) : max(0, end)]
    if not segment:
        return None, None
    return max(_fnum(row[2]) for row in segment), min(_fnum(row[3]) for row in segment)


def _swing_failure(rows: list[list[Any]], idx: int, *, lookback: int) -> str:
    if idx <= 0:
        return ""
    prev_high, prev_low = _recent_extremes(rows, idx - lookback, idx)
    if prev_high is None or prev_low is None:
        return ""
    row = rows[idx]
    high = _fnum(row[2])
    low = _fnum(row[3])
    close_px = _fnum(row[4])
    if high > prev_high and close_px < prev_high:
        return "bearish"
    if low < prev_low and close_px > prev_low:
        return "bullish"
    return ""


def _range_acceptance(rows: list[list[Any]], idx: int, *, lookback: int) -> str:
    if idx <= 0:
        return ""
    prev_high, prev_low = _recent_extremes(rows, idx - lookback, idx)
    if prev_high is None or prev_low is None:
        return ""
    row = rows[idx]
    close_px = _fnum(row[4])
    high = _fnum(row[2])
    low = _fnum(row[3])
    if close_px > prev_high:
        return "acceptance_above"
    if close_px < prev_low:
        return "acceptance_below"
    if high > prev_high and close_px <= prev_high:
        return "rejection_above"
    if low < prev_low and close_px >= prev_low:
        return "rejection_below"
    return ""


def _fair_value_gap(rows: list[list[Any]], idx: int) -> str:
    if idx < 2:
        return ""
    left = rows[idx - 2]
    cur = rows[idx]
    if _fnum(cur[3]) > _fnum(left[2]):
        return "bullish"
    if _fnum(cur[2]) < _fnum(left[3]):
        return "bearish"
    return ""


def _displacement(rows: list[list[Any]], idx: int, *, lookback: int, range_multiple: float, min_body_fraction: float) -> bool:
    if idx <= 0:
        return False
    recent = rows[max(0, idx - lookback) : idx]
    avg_range = _avg([_range(row) for row in recent])
    cur_range = _range(rows[idx])
    if avg_range <= 0.0 or cur_range < avg_range * range_multiple:
        return False
    return (_body(rows[idx]) / max(cur_range, 1e-12)) >= min_body_fraction


def _break_retest(rows: list[list[Any]], idx: int, *, lookback: int) -> str:
    if idx <= 0:
        return ""
    prior_idx = idx - 1
    prior_high, prior_low = _recent_extremes(rows, prior_idx - lookback, prior_idx)
    if prior_high is None or prior_low is None:
        return ""
    prev = rows[prior_idx]
    cur = rows[idx]
    prev_close = _fnum(prev[4])
    cur_low = _fnum(cur[3])
    cur_high = _fnum(cur[2])
    cur_close = _fnum(cur[4])
    if prev_close > prior_high and cur_low <= prior_high <= cur_close:
        return "bullish_hold"
    if prev_close < prior_low and cur_high >= prior_low >= cur_close:
        return "bearish_hold"
    return ""


def _opening_range_states(rows: list[list[Any]], *, opening_range_bars: int) -> dict[int, dict[str, Any]]:
    by_day: dict[str, list[tuple[int, list[Any]]]] = {}
    for idx, row in enumerate(rows):
        by_day.setdefault(_utc_day(_safe_ts_ms(row)), []).append((idx, row))

    out: dict[int, dict[str, Any]] = {}
    for day, indexed in by_day.items():
        if not day or not indexed:
            continue
        opening = indexed[: max(1, int(opening_range_bars))]
        opening_high = max(_fnum(row[2]) for _, row in opening)
        opening_low = min(_fnum(row[3]) for _, row in opening)
        state = "forming"
        for day_pos, (idx, row) in enumerate(indexed):
            close_px = _fnum(row[4])
            if day_pos < len(opening):
                state = "forming"
            elif close_px > opening_high:
                state = "acceptance_above"
            elif close_px < opening_low:
                state = "acceptance_below"
            elif _fnum(row[2]) > opening_high:
                state = "rejection_above"
            elif _fnum(row[3]) < opening_low:
                state = "rejection_below"
            out[idx] = {
                "session_date": day,
                "opening_range_high": float(opening_high),
                "opening_range_low": float(opening_low),
                "opening_range_state": state,
            }
    return out


def label_price_action_context(
    rows: list[list[Any]],
    *,
    swing_lookback: int = 5,
    range_lookback: int = 5,
    displacement_lookback: int = 10,
    displacement_range_multiple: float = 1.5,
    displacement_min_body_fraction: float = 0.6,
    rejection_wick_body_multiple: float = 2.0,
    rejection_wick_range_fraction: float = 0.45,
    opening_range_bars: int = 3,
) -> list[dict[str, Any]]:
    clean = normalize_ohlcv_rows(rows)
    opening = _opening_range_states(clean, opening_range_bars=opening_range_bars)
    labels: list[dict[str, Any]] = []
    for idx, row in enumerate(clean):
        ts_ms = _safe_ts_ms(row)
        label = {
            "idx": idx,
            "ts_ms": ts_ms,
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": row[5] if len(row) > 5 else None,
            "candle_direction": _direction(row),
            "engulfing_candle": _engulfing(clean, idx),
            "rejection_wick": _rejection_wick(
                row,
                body_multiple=float(rejection_wick_body_multiple),
                range_fraction=float(rejection_wick_range_fraction),
            ),
            "swing_failure": _swing_failure(clean, idx, lookback=max(1, int(swing_lookback))),
            "break_and_retest": _break_retest(clean, idx, lookback=max(1, int(range_lookback))),
            "fair_value_gap": _fair_value_gap(clean, idx),
            "displacement_bar": _displacement(
                clean,
                idx,
                lookback=max(1, int(displacement_lookback)),
                range_multiple=max(0.0, float(displacement_range_multiple)),
                min_body_fraction=max(0.0, float(displacement_min_body_fraction)),
            ),
            "acceptance_rejection": _range_acceptance(clean, idx, lookback=max(1, int(range_lookback))),
            "volume_profile_acceptance": "requires_trade_or_tick_volume_profile",
            "manipulation_candidate": (
                "liquidity_sweep_reversal"
                if _swing_failure(clean, idx, lookback=max(1, int(swing_lookback))) and _displacement(
                    clean,
                    idx,
                    lookback=max(1, int(displacement_lookback)),
                    range_multiple=max(0.0, float(displacement_range_multiple)),
                    min_body_fraction=max(0.0, float(displacement_min_body_fraction)),
                )
                else ""
            ),
        }
        label.update(opening.get(idx) or {"session_date": _utc_day(ts_ms), "opening_range_state": ""})
        labels.append(label)
    return labels


def _label_counts(labels: list[dict[str, Any]]) -> dict[str, int]:
    keys = [
        "engulfing_candle",
        "rejection_wick",
        "swing_failure",
        "break_and_retest",
        "fair_value_gap",
        "displacement_bar",
        "acceptance_rejection",
        "opening_range_state",
        "volume_profile_acceptance",
        "manipulation_candidate",
    ]
    counts: dict[str, int] = {}
    for key in keys:
        count = 0
        for row in labels:
            value = row.get(key)
            if key == "volume_profile_acceptance" and str(value or "").startswith("requires_"):
                continue
            if isinstance(value, bool):
                count += int(value)
            elif str(value or "").strip():
                count += 1
        counts[key] = int(count)
    return counts


def price_action_artifact_hash(payload: dict[str, Any]) -> str:
    stripped = {k: v for k, v in dict(payload).items() if k not in {"artifact_hash", "generated_at"}}
    encoded = json.dumps(stripped, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_price_action_context_artifact(
    rows: list[list[Any]],
    *,
    venue: str,
    symbol: str,
    timeframe: str,
    source: str = "market_ohlcv_archive",
    dataset_hash: str | None = None,
    archive_path: str = "",
    generated_at: str | None = None,
    **label_kwargs: Any,
) -> dict[str, Any]:
    clean = normalize_ohlcv_rows(rows)
    labels = label_price_action_context(clean, **label_kwargs)
    ds_hash = str(
        dataset_hash
        or ohlcv_dataset_hash(
            venue=venue,
            symbol=symbol,
            timeframe=timeframe,
            rows=clean,
            source=source,
        )
    )
    payload: dict[str, Any] = {
        "ok": bool(labels),
        "artifact_type": ARTIFACT_TYPE,
        "research_only": True,
        "limitations": list(LIMITATIONS),
        "source": str(source),
        "dataset_hash": ds_hash,
        "archive_path": str(archive_path or ""),
        "venue": normalize_venue(venue),
        "symbol": normalize_symbol(symbol),
        "timeframe": str(timeframe),
        "row_count": int(len(clean)),
        "label_count": int(len(labels)),
        "label_counts": _label_counts(labels),
        "labels": labels,
        "volume_profile_policy": "deferred_until_trade_tick_or_profile_data",
        "databento_policy": "separate_data_source_rfc_required",
    }
    if generated_at:
        payload["generated_at"] = str(generated_at)
    payload["artifact_hash"] = price_action_artifact_hash(payload)
    return payload
