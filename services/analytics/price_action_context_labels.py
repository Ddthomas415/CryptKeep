from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.backtest.ohlcv_archive import load_archived_ohlcv, normalize_ohlcv_rows, ohlcv_dataset_hash


ARTIFACT_TYPE = "price_action_context_labels_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _iso_ms(ts_ms: int) -> str:
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _session_key(ts_ms: int) -> str:
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=timezone.utc).date().isoformat()


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _candle(row: list[Any]) -> dict[str, float | int | None]:
    return {
        "ts_ms": int(row[0]),
        "open": float(row[1]),
        "high": float(row[2]),
        "low": float(row[3]),
        "close": float(row[4]),
        "volume": None if len(row) < 6 or row[5] is None else float(row[5]),
    }


def _body(c: dict[str, Any]) -> float:
    return abs(float(c["close"]) - float(c["open"]))


def _range(c: dict[str, Any]) -> float:
    return max(0.0, float(c["high"]) - float(c["low"]))


def _body_top(c: dict[str, Any]) -> float:
    return max(float(c["open"]), float(c["close"]))


def _body_bottom(c: dict[str, Any]) -> float:
    return min(float(c["open"]), float(c["close"]))


def _avg_range(candles: list[dict[str, Any]], idx: int, lookback: int) -> float | None:
    start = max(0, idx - max(1, int(lookback)))
    window = candles[start:idx]
    ranges = [_range(c) for c in window if _range(c) > 0.0]
    if not ranges:
        return None
    return float(sum(ranges) / len(ranges))


def _engulfing(candles: list[dict[str, Any]], idx: int) -> str | None:
    if idx <= 0:
        return None
    prev = candles[idx - 1]
    cur = candles[idx]
    covers_body = _body_bottom(cur) <= _body_bottom(prev) and _body_top(cur) >= _body_top(prev)
    if not covers_body or _body(cur) <= _body(prev):
        return None
    if float(cur["close"]) > float(cur["open"]) and float(prev["close"]) < float(prev["open"]):
        return "bullish"
    if float(cur["close"]) < float(cur["open"]) and float(prev["close"]) > float(prev["open"]):
        return "bearish"
    return None


def _rejection_wick(
    candle: dict[str, Any],
    *,
    min_wick_body_ratio: float,
    min_wick_range_ratio: float,
) -> str | None:
    body = max(_body(candle), 1e-12)
    rng = max(_range(candle), 1e-12)
    upper = float(candle["high"]) - _body_top(candle)
    lower = _body_bottom(candle) - float(candle["low"])
    upper_ok = upper / body >= min_wick_body_ratio and upper / rng >= min_wick_range_ratio
    lower_ok = lower / body >= min_wick_body_ratio and lower / rng >= min_wick_range_ratio
    if upper_ok and lower_ok:
        return "both"
    if upper_ok:
        return "upper"
    if lower_ok:
        return "lower"
    return None


def _fair_value_gap(candles: list[dict[str, Any]], idx: int) -> str | None:
    if idx < 2:
        return None
    left = candles[idx - 2]
    cur = candles[idx]
    if float(cur["low"]) > float(left["high"]):
        return "bullish"
    if float(cur["high"]) < float(left["low"]):
        return "bearish"
    return None


def _swing_failure(candles: list[dict[str, Any]], idx: int, *, swing_lookback: int) -> str | None:
    if idx <= 0:
        return None
    start = max(0, idx - max(1, int(swing_lookback)))
    window = candles[start:idx]
    if not window:
        return None
    prior_high = max(float(c["high"]) for c in window)
    prior_low = min(float(c["low"]) for c in window)
    cur = candles[idx]
    if float(cur["high"]) > prior_high and float(cur["close"]) < prior_high:
        return "bearish"
    if float(cur["low"]) < prior_low and float(cur["close"]) > prior_low:
        return "bullish"
    return None


def _break_and_retest(candles: list[dict[str, Any]], idx: int, *, swing_lookback: int) -> str | None:
    if idx < 2:
        return None
    start = max(0, idx - max(1, int(swing_lookback)) - 1)
    window = candles[start : idx - 1]
    if not window:
        return None
    prior_high = max(float(c["high"]) for c in window)
    prior_low = min(float(c["low"]) for c in window)
    prev = candles[idx - 1]
    cur = candles[idx]
    if float(prev["close"]) > prior_high and float(cur["low"]) <= prior_high:
        return "bullish_hold" if float(cur["close"]) > prior_high else "bullish_reject"
    if float(prev["close"]) < prior_low and float(cur["high"]) >= prior_low:
        return "bearish_hold" if float(cur["close"]) < prior_low else "bearish_reject"
    return None


def _displacement(candles: list[dict[str, Any]], idx: int, *, range_lookback: int, range_multiplier: float, min_body_ratio: float) -> str | None:
    avg = _avg_range(candles, idx, range_lookback)
    if avg is None or avg <= 0.0:
        return None
    cur = candles[idx]
    rng = _range(cur)
    if rng < avg * float(range_multiplier):
        return None
    if _body(cur) / max(rng, 1e-12) < float(min_body_ratio):
        return None
    if float(cur["close"]) > float(cur["open"]):
        return "bullish"
    if float(cur["close"]) < float(cur["open"]):
        return "bearish"
    return "neutral"


def _opening_range_states(candles: list[dict[str, Any]], *, opening_range_bars: int) -> dict[int, str]:
    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for idx, candle in enumerate(candles):
        grouped[_session_key(int(candle["ts_ms"]))].append((idx, candle))

    out: dict[int, str] = {}
    bars = max(1, int(opening_range_bars))
    for group in grouped.values():
        opening = group[:bars]
        if not opening:
            continue
        high = max(float(c["high"]) for _, c in opening)
        low = min(float(c["low"]) for _, c in opening)
        for offset, (idx, candle) in enumerate(group):
            if offset < bars:
                out[idx] = "forming"
                continue
            close = float(candle["close"])
            candle_high = float(candle["high"])
            candle_low = float(candle["low"])
            if close > high:
                out[idx] = "accepted_above"
            elif candle_high > high and close <= high:
                out[idx] = "rejected_above"
            elif close < low:
                out[idx] = "accepted_below"
            elif candle_low < low and close >= low:
                out[idx] = "rejected_below"
            else:
                out[idx] = "inside"
    return out


def build_price_action_context_labels(
    *,
    venue: str,
    symbol: str,
    timeframe: str,
    rows: list[list[Any]],
    source: str = "provided_ohlcv",
    dataset_hash: str | None = None,
    swing_lookback: int = 5,
    range_lookback: int = 10,
    displacement_range_multiplier: float = 1.8,
    displacement_min_body_ratio: float = 0.6,
    rejection_min_wick_body_ratio: float = 2.0,
    rejection_min_wick_range_ratio: float = 0.35,
    opening_range_bars: int = 3,
    min_rows: int = 3,
) -> dict[str, Any]:
    clean_rows = normalize_ohlcv_rows(list(rows or []))
    resolved_dataset_hash = dataset_hash or ohlcv_dataset_hash(
        venue=venue,
        symbol=symbol,
        timeframe=timeframe,
        rows=clean_rows,
        source=source,
    )
    if len(clean_rows) < max(3, int(min_rows)):
        return {
            "artifact_type": ARTIFACT_TYPE,
            "ok": False,
            "reason": "insufficient_ohlcv_rows",
            "research_only": True,
            "not_strategy_config": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
            "not_profitability_evidence": True,
            "venue": str(venue),
            "symbol": str(symbol),
            "timeframe": str(timeframe),
            "source": str(source),
            "dataset_hash": resolved_dataset_hash,
            "row_count": len(clean_rows),
            "labels": [],
        }

    candles = [_candle(row) for row in clean_rows]
    opening_states = _opening_range_states(candles, opening_range_bars=opening_range_bars)
    labels: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for idx, candle in enumerate(candles):
        engulfing = _engulfing(candles, idx)
        rejection = _rejection_wick(
            candle,
            min_wick_body_ratio=rejection_min_wick_body_ratio,
            min_wick_range_ratio=rejection_min_wick_range_ratio,
        )
        fvg = _fair_value_gap(candles, idx)
        swing = _swing_failure(candles, idx, swing_lookback=swing_lookback)
        retest = _break_and_retest(candles, idx, swing_lookback=swing_lookback)
        displacement = _displacement(
            candles,
            idx,
            range_lookback=range_lookback,
            range_multiplier=displacement_range_multiplier,
            min_body_ratio=displacement_min_body_ratio,
        )
        manipulation = None
        if swing == "bearish" and (rejection in {"upper", "both"} or displacement == "bearish"):
            manipulation = "bearish_sweep_reversal"
        elif swing == "bullish" and (rejection in {"lower", "both"} or displacement == "bullish"):
            manipulation = "bullish_sweep_reversal"

        row_labels = {
            "engulfing_candle": engulfing,
            "rejection_wick": rejection,
            "fair_value_gap": fvg,
            "swing_failure": swing,
            "break_and_retest": retest,
            "displacement_bar": displacement,
            "manipulation_candidate": manipulation,
            "opening_range_state": opening_states.get(idx),
        }
        for name, value in row_labels.items():
            if value:
                counts[f"{name}:{value}"] += 1
        labels.append(
            {
                "ts_ms": int(candle["ts_ms"]),
                "ts": _iso_ms(int(candle["ts_ms"])),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
                "volume": candle["volume"],
                "labels": row_labels,
            }
        )

    label_payload = {
        "source": source,
        "dataset_hash": resolved_dataset_hash,
        "params": {
            "swing_lookback": int(swing_lookback),
            "range_lookback": int(range_lookback),
            "displacement_range_multiplier": float(displacement_range_multiplier),
            "displacement_min_body_ratio": float(displacement_min_body_ratio),
            "rejection_min_wick_body_ratio": float(rejection_min_wick_body_ratio),
            "rejection_min_wick_range_ratio": float(rejection_min_wick_range_ratio),
            "opening_range_bars": int(opening_range_bars),
        },
        "labels": labels,
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
        "venue": str(venue),
        "symbol": str(symbol),
        "timeframe": str(timeframe),
        "source": str(source),
        "dataset_hash": resolved_dataset_hash,
        "artifact_hash": _sha(label_payload),
        "row_count": len(labels),
        "label_counts": dict(sorted(counts.items())),
        "labels": labels,
        "limitations": [
            "ohlcv_only_descriptive_context_labels",
            "not_trade_signals",
            "not_strategy_authority",
            "join_to_forward_returns_before_strategy_use",
            "volume_profile_deferred_requires_stronger_intraday_volume_or_trades",
            "databento_deferred_to_separate_data_source_rfc",
        ],
    }


def run_archive_price_action_context_labels(
    *,
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
    db_path: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    loaded = load_archived_ohlcv(
        venue,
        symbol,
        timeframe=str(timeframe),
        limit=int(max(1, limit)),
        since_ms=since_ms,
        db_path=db_path,
    )
    if not (loaded.get("ok") and loaded.get("complete")):
        return {
            "artifact_type": ARTIFACT_TYPE,
            "ok": False,
            "reason": str(loaded.get("reason") or "archive_unavailable"),
            "research_only": True,
            "not_strategy_config": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
            "not_profitability_evidence": True,
            "archive": {k: v for k, v in dict(loaded).items() if k != "rows"},
            "labels": [],
        }
    report = build_price_action_context_labels(
        venue=str(loaded.get("exchange") or venue),
        symbol=str(loaded.get("symbol") or symbol),
        timeframe=str(loaded.get("timeframe") or timeframe),
        rows=list(loaded.get("rows") or []),
        source=str(loaded.get("source") or "market_ohlcv_archive"),
        dataset_hash=str(loaded.get("dataset_hash") or ""),
        **kwargs,
    )
    report["archive"] = {k: v for k, v in dict(loaded).items() if k != "rows"}
    return report
