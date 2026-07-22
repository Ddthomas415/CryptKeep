from __future__ import annotations

import datetime as dt
import math
from typing import Any

from services.backtest.ohlcv_archive import (
    ARCHIVE_SOURCE,
    load_archived_ohlcv,
    normalize_ohlcv_rows,
    ohlcv_dataset_hash,
)
from services.market_data.symbol_router import normalize_symbol, normalize_venue


ARTIFACT_TYPE = "price_action_context_labels_v1"

LIMITATION_FLAGS: dict[str, bool] = {
    "research_only": True,
    "not_strategy_config": True,
    "not_campaign_evidence": True,
    "not_promotion_evidence": True,
    "not_profitability_evidence": True,
}

DEFAULT_SWING_LOOKBACK = 5
DEFAULT_DISPLACEMENT_LOOKBACK = 10
DEFAULT_OPENING_RANGE_BARS = 6
DEFAULT_WICK_BODY_RATIO = 2.0
DEFAULT_WICK_RANGE_RATIO = 0.45
DEFAULT_DISPLACEMENT_RANGE_MULTIPLIER = 1.5
DEFAULT_DISPLACEMENT_BODY_FRACTION = 0.55


def _f(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def _positive_int(value: Any, default: int, *, minimum: int = 1) -> int:
    try:
        out = int(value)
    except Exception:
        return int(default)
    return max(int(minimum), out)


def _ohlcv(row: list[Any]) -> tuple[int, float, float, float, float, float | None]:
    ts = int(float(row[0]))
    if ts < 10_000_000_000:
        ts *= 1000
    vol = None if len(row) < 6 or row[5] is None else _f(row[5])
    return ts, _f(row[1]), _f(row[2]), _f(row[3]), _f(row[4]), vol


def _body(open_px: float, close_px: float) -> float:
    return abs(float(close_px) - float(open_px))


def _candle_range(high_px: float, low_px: float) -> float:
    return max(0.0, float(high_px) - float(low_px))


def _direction(open_px: float, close_px: float) -> str:
    if close_px > open_px:
        return "bullish"
    if close_px < open_px:
        return "bearish"
    return "doji"


def _engulfing(rows: list[list[Any]], idx: int) -> str | None:
    if idx < 1:
        return None
    _ts, o, _h, _l, c, _v = _ohlcv(rows[idx])
    _pts, po, _ph, _pl, pc, _pv = _ohlcv(rows[idx - 1])
    cur_low = min(o, c)
    cur_high = max(o, c)
    prev_low = min(po, pc)
    prev_high = max(po, pc)
    if cur_low <= prev_low and cur_high >= prev_high and _body(o, c) > 0:
        direction = _direction(o, c)
        return None if direction == "doji" else direction
    return None


def _rejection_wick(
    row: list[Any],
    *,
    wick_body_ratio: float,
    wick_range_ratio: float,
) -> str | None:
    _ts, o, h, l, c, _v = _ohlcv(row)
    body = max(_body(o, c), 1e-12)
    candle_range = max(_candle_range(h, l), 1e-12)
    upper = max(0.0, h - max(o, c))
    lower = max(0.0, min(o, c) - l)
    upper_ok = upper >= wick_body_ratio * body and upper / candle_range >= wick_range_ratio
    lower_ok = lower >= wick_body_ratio * body and lower / candle_range >= wick_range_ratio
    if upper_ok and lower_ok:
        return "both"
    if lower_ok:
        return "bullish_lower"
    if upper_ok:
        return "bearish_upper"
    return None


def _recent_level(
    rows: list[list[Any]],
    idx: int,
    lookback: int,
    field_idx: int,
    fn: Any,
) -> float | None:
    start = max(0, idx - lookback)
    window = rows[start:idx]
    if len(window) < lookback:
        return None
    try:
        return float(fn(float(row[field_idx]) for row in window))
    except Exception:
        return None


def _swing_failure(rows: list[list[Any]], idx: int, lookback: int) -> str | None:
    if idx < lookback:
        return None
    _ts, _o, h, l, c, _v = _ohlcv(rows[idx])
    recent_high = _recent_level(rows, idx, lookback, 2, max)
    recent_low = _recent_level(rows, idx, lookback, 3, min)
    if recent_high is not None and h > recent_high and c < recent_high:
        return "bearish"
    if recent_low is not None and l < recent_low and c > recent_low:
        return "bullish"
    return None


def _break_and_retest(rows: list[list[Any]], idx: int, lookback: int) -> str | None:
    if idx < lookback + 1:
        return None
    _pts, _po, _ph, _pl, pc, _pv = _ohlcv(rows[idx - 1])
    _ts, _o, h, l, c, _v = _ohlcv(rows[idx])
    prior_high = _recent_level(rows, idx - 1, lookback, 2, max)
    prior_low = _recent_level(rows, idx - 1, lookback, 3, min)
    if prior_high is not None and pc > prior_high and l <= prior_high:
        return "bullish_hold" if c >= prior_high else "bullish_rejected"
    if prior_low is not None and pc < prior_low and h >= prior_low:
        return "bearish_hold" if c <= prior_low else "bearish_rejected"
    return None


def _fair_value_gap(rows: list[list[Any]], idx: int) -> str | None:
    if idx < 2:
        return None
    _ts, _o, h, l, _c, _v = _ohlcv(rows[idx])
    _t0, _o0, h0, l0, _c0, _v0 = _ohlcv(rows[idx - 2])
    if l > h0:
        return "bullish"
    if h < l0:
        return "bearish"
    return None


def _displacement_bar(
    rows: list[list[Any]],
    idx: int,
    lookback: int,
    range_multiplier: float,
    body_fraction: float,
) -> bool:
    if idx < lookback:
        return False
    _ts, o, h, l, c, _v = _ohlcv(rows[idx])
    recent_ranges = [
        _candle_range(float(row[2]), float(row[3]))
        for row in rows[max(0, idx - lookback):idx]
    ]
    avg_range = sum(recent_ranges) / max(1, len(recent_ranges))
    cur_range = _candle_range(h, l)
    if avg_range <= 0.0 or cur_range < range_multiplier * avg_range:
        return False
    return (_body(o, c) / max(cur_range, 1e-12)) >= body_fraction


def _opening_range_state(
    rows: list[list[Any]],
    idx: int,
    opening_range_bars: int,
) -> tuple[str | None, str | None, float | None, float | None]:
    if opening_range_bars <= 0:
        return None, None, None, None
    if len(rows) < opening_range_bars:
        return "forming", None, None, None
    opening = rows[:opening_range_bars]
    opening_high = max(float(row[2]) for row in opening)
    opening_low = min(float(row[3]) for row in opening)
    _ts, _o, h, l, c, _v = _ohlcv(rows[idx])
    if idx < opening_range_bars:
        return "forming", None, opening_high, opening_low
    if c > opening_high:
        return "accepted_above", "acceptance_above_opening_range", opening_high, opening_low
    if c < opening_low:
        return "accepted_below", "acceptance_below_opening_range", opening_high, opening_low
    if h > opening_high and c <= opening_high:
        return "rejected_above", "rejection_above_opening_range", opening_high, opening_low
    if l < opening_low and c >= opening_low:
        return "rejected_below", "rejection_below_opening_range", opening_high, opening_low
    return "inside", None, opening_high, opening_low


def _label_counts(labels: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in labels:
        for key, value in dict(row.get("labels") or {}).items():
            if value is None or value is False or value == "":
                continue
            suffix = str(value).lower() if not isinstance(value, bool) else "true"
            name = f"{key}:{suffix}"
            counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def _resolved_label_config(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = dict(cfg or {})
    return {
        "swing_lookback": _positive_int(
            raw.get("swing_lookback", DEFAULT_SWING_LOOKBACK),
            DEFAULT_SWING_LOOKBACK,
        ),
        "displacement_lookback": _positive_int(
            raw.get("displacement_lookback", DEFAULT_DISPLACEMENT_LOOKBACK),
            DEFAULT_DISPLACEMENT_LOOKBACK,
        ),
        "opening_range_bars": _positive_int(
            raw.get("opening_range_bars", DEFAULT_OPENING_RANGE_BARS),
            DEFAULT_OPENING_RANGE_BARS,
            minimum=0,
        ),
        "wick_body_ratio": max(
            0.1,
            _f(raw.get("wick_body_ratio", DEFAULT_WICK_BODY_RATIO), DEFAULT_WICK_BODY_RATIO),
        ),
        "wick_range_ratio": min(
            1.0,
            max(
                0.0,
                _f(
                    raw.get("wick_range_ratio", DEFAULT_WICK_RANGE_RATIO),
                    DEFAULT_WICK_RANGE_RATIO,
                ),
            ),
        ),
        "displacement_range_multiplier": max(
            0.1,
            _f(
                raw.get(
                    "displacement_range_multiplier",
                    DEFAULT_DISPLACEMENT_RANGE_MULTIPLIER,
                ),
                DEFAULT_DISPLACEMENT_RANGE_MULTIPLIER,
            ),
        ),
        "displacement_body_fraction": min(
            1.0,
            max(
                0.0,
                _f(
                    raw.get(
                        "displacement_body_fraction",
                        DEFAULT_DISPLACEMENT_BODY_FRACTION,
                    ),
                    DEFAULT_DISPLACEMENT_BODY_FRACTION,
                ),
            ),
        ),
    }


def compute_price_action_labels(
    rows: list[list[Any]],
    *,
    swing_lookback: int = DEFAULT_SWING_LOOKBACK,
    displacement_lookback: int = DEFAULT_DISPLACEMENT_LOOKBACK,
    opening_range_bars: int = DEFAULT_OPENING_RANGE_BARS,
    wick_body_ratio: float = DEFAULT_WICK_BODY_RATIO,
    wick_range_ratio: float = DEFAULT_WICK_RANGE_RATIO,
    displacement_range_multiplier: float = DEFAULT_DISPLACEMENT_RANGE_MULTIPLIER,
    displacement_body_fraction: float = DEFAULT_DISPLACEMENT_BODY_FRACTION,
) -> list[dict[str, Any]]:
    clean = normalize_ohlcv_rows(rows)
    resolved = _resolved_label_config(
        {
            "swing_lookback": swing_lookback,
            "displacement_lookback": displacement_lookback,
            "opening_range_bars": opening_range_bars,
            "wick_body_ratio": wick_body_ratio,
            "wick_range_ratio": wick_range_ratio,
            "displacement_range_multiplier": displacement_range_multiplier,
            "displacement_body_fraction": displacement_body_fraction,
        }
    )
    swing_lb = int(resolved["swing_lookback"])
    displacement_lb = int(resolved["displacement_lookback"])
    opening_bars = int(resolved["opening_range_bars"])
    wick_body = float(resolved["wick_body_ratio"])
    wick_range = float(resolved["wick_range_ratio"])
    displacement_mult = float(resolved["displacement_range_multiplier"])
    body_fraction = float(resolved["displacement_body_fraction"])

    out: list[dict[str, Any]] = []
    for idx, row in enumerate(clean):
        ts, o, h, l, c, vol = _ohlcv(row)
        opening_state, acceptance_rejection, opening_high, opening_low = _opening_range_state(
            clean,
            idx,
            opening_bars,
        )
        displacement = _displacement_bar(clean, idx, displacement_lb, displacement_mult, body_fraction)
        swing_failure = _swing_failure(clean, idx, swing_lb)
        manipulation_candidate = (
            "liquidity_sweep_reversal"
            if swing_failure and displacement
            else None
        )
        out.append(
            {
                "ts_ms": ts,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": vol,
                "labels": {
                    "engulfing_candle": _engulfing(clean, idx),
                    "rejection_wick": _rejection_wick(
                        row,
                        wick_body_ratio=wick_body,
                        wick_range_ratio=wick_range,
                    ),
                    "swing_failure": swing_failure,
                    "break_and_retest": _break_and_retest(clean, idx, swing_lb),
                    "fair_value_gap": _fair_value_gap(clean, idx),
                    "displacement_bar": displacement,
                    "opening_range_state": opening_state,
                    "acceptance_rejection": acceptance_rejection,
                    "manipulation_candidate": manipulation_candidate,
                },
                "metrics": {
                    "body": _body(o, c),
                    "range": _candle_range(h, l),
                    "direction": _direction(o, c),
                    "opening_range_high": opening_high,
                    "opening_range_low": opening_low,
                },
            }
        )
    return out


def build_price_action_context_artifact(
    *,
    rows: list[list[Any]],
    venue: str,
    symbol: str,
    timeframe: str,
    source: str = ARCHIVE_SOURCE,
    dataset_hash: str | None = None,
    archive_path: str | None = None,
    session_calendar_policy: str = "input_window_first_n_bars",
    label_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean = normalize_ohlcv_rows(rows)
    cfg = dict(label_config or {})
    exchange = normalize_venue(venue)
    canonical_symbol = normalize_symbol(symbol)
    labels = compute_price_action_labels(clean, **cfg)
    data_hash = dataset_hash or ohlcv_dataset_hash(
        venue=exchange,
        symbol=canonical_symbol,
        timeframe=str(timeframe),
        rows=clean,
        source=str(source or ARCHIVE_SOURCE),
    )
    start_ts = int(clean[0][0]) if clean else None
    end_ts = int(clean[-1][0]) if clean else None
    return {
        "ok": bool(clean),
        "reason": "ok" if clean else "no_rows",
        "artifact_type": ARTIFACT_TYPE,
        **LIMITATION_FLAGS,
        "limitation_flags": dict(LIMITATION_FLAGS),
        "generated_at": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        "venue": exchange,
        "symbol": canonical_symbol,
        "timeframe": str(timeframe),
        "session_calendar_policy": str(session_calendar_policy),
        "dataset": {
            "source": str(source or ARCHIVE_SOURCE),
            "archive_path": archive_path,
            "dataset_hash": data_hash,
            "bars": int(len(clean)),
            "start_ts_ms": start_ts,
            "end_ts_ms": end_ts,
        },
        "label_config": _resolved_label_config(cfg),
        "deferred_data_sources": {
            "volume_profile_acceptance": "deferred_requires_trade_or_tick_data",
            "databento": "deferred_requires_separate_read_only_data_source_rfc",
            "microstructure": "deferred_requires_bid_ask_trade_or_order_book_data",
        },
        "label_counts": _label_counts(labels),
        "labels": labels,
    }


def run_archive_price_action_context(
    *,
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
    db_path: str | None = None,
    label_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    archive = load_archived_ohlcv(
        venue=str(venue),
        canonical_symbol=str(symbol),
        timeframe=str(timeframe),
        limit=int(limit),
        since_ms=since_ms,
        db_path=db_path,
    )
    if not bool(archive.get("ok")):
        return {
            "ok": False,
            "reason": str(archive.get("reason") or "archive_unavailable"),
            "artifact_type": ARTIFACT_TYPE,
            **LIMITATION_FLAGS,
            "limitation_flags": dict(LIMITATION_FLAGS),
            "venue": normalize_venue(venue),
            "symbol": normalize_symbol(symbol),
            "timeframe": str(timeframe),
            "dataset": {
                "source": str(archive.get("source") or ARCHIVE_SOURCE),
                "archive_path": archive.get("archive_path"),
                "dataset_hash": None,
                "bars": int(len(list(archive.get("rows") or []))),
                "start_ts_ms": None,
                "end_ts_ms": None,
            },
            "labels": [],
            "label_counts": {},
        }
    return build_price_action_context_artifact(
        rows=list(archive.get("rows") or []),
        venue=str(archive.get("exchange") or venue),
        symbol=str(archive.get("symbol") or symbol),
        timeframe=str(archive.get("timeframe") or timeframe),
        source=str(archive.get("source") or ARCHIVE_SOURCE),
        dataset_hash=str(archive.get("dataset_hash") or ""),
        archive_path=str(archive.get("archive_path") or ""),
        label_config=label_config,
    )
