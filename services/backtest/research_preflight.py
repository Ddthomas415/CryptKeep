"""Research eligibility checks; not a trading or promotion gate."""
from __future__ import annotations

import copy
import inspect
import math
import re

from services.strategies import breakout_donchian, ema_cross, es_daily_trend


def resolve_research_config(cfg: dict) -> dict:
    if not isinstance(cfg, dict):
        raise ValueError("invalid_research_config")
    resolved = copy.deepcopy(cfg)
    st = resolved.get("strategy")
    if not isinstance(st, dict) or not st.get("name"):
        raise ValueError("strategy_identity_missing")
    families = {
        "breakout_donchian": {"donchian_len"},
        "ema_cross": {"ema_fast", "ema_slow"},
        "sma_200_trend": {"sma_period", "atr_period"},
    }
    if not isinstance(st["name"], str) or st["name"] not in families:
        raise ValueError("unsupported_research_strategy")
    if st.get("trade_enabled", True) is not True:
        raise ValueError("research_strategy_disabled_or_invalid")
    filters = {"filter_window", "min_volatility_pct", "min_volume_ratio",
               "min_trend_efficiency", "min_channel_width_pct", "breakout_buffer_pct",
               "require_directional_confirmation"}
    if st["name"] == "ema_cross":
        filters = {"filter_window", "min_volatility_pct", "min_volume_ratio",
                   "min_trend_efficiency", "min_cross_gap_pct"}
    elif st["name"] == "sma_200_trend":
        filters = set()
    metadata = {"name", "id", "version", "stage", "symbol", "venue", "trade_enabled",
                "emit_evidence", "research_only_override", "signal", "no_trade_filters"}
    unknown = set(st) - metadata - families[st["name"]] - filters
    if unknown:
        raise ValueError(f"unsupported_strategy_parameter:{sorted(unknown)[0]}")
    for section, allowed in (("signal", families.get(st["name"], set())),
                             ("no_trade_filters", filters)):
        nested = st.get(section, {})
        if not isinstance(nested, dict):
            raise ValueError(f"invalid_strategy_section:{section}")
        if nested and st["name"] == "sma_200_trend":
            raise ValueError(f"unsupported_nested_strategy:{st['name']}")
        for key, value in nested.items():
            if section == "signal" and key in {"type", "direction"}:
                expected = ("donchian_breakout" if st["name"] == "breakout_donchian" else "ema_cross") if key == "type" else "long_flat_only"
                if value != expected:
                    raise ValueError(f"unsupported_signal_metadata:{key}")
                continue
            if key not in allowed:
                raise ValueError(f"unsupported_nested_parameter:{key}")
            if key in st and (type(st[key]) is not type(value) or st[key] != value):
                raise ValueError(f"conflicting_strategy_parameter:{key}")
            st[key] = value
    for key in families.get(st["name"], set()) | filters:
        if key not in st:
            continue
        value = st[key]
        if key == "require_directional_confirmation":
            valid = type(value) is bool
        else:
            valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
            if key in {"donchian_len", "ema_fast", "ema_slow", "filter_window", "sma_period", "atr_period"}:
                valid = valid and value >= 2 and int(value) == value
        if not valid:
            raise ValueError(f"invalid_strategy_parameter:{key}")
    return resolved


def check_research_history(cfg: dict, *, row_count: int, warmup_bars: int, min_train_bars: int) -> int:
    st = cfg["strategy"]
    name = st["name"]
    fn = {"ema_cross": ema_cross.signal_from_ohlcv,
          "breakout_donchian": breakout_donchian.signal_from_ohlcv,
          "sma_200_trend": es_daily_trend.signal_from_ohlcv}[name]
    params = inspect.signature(fn).parameters
    def period(key):
        return int(st.get(key, params[key].default))
    if name == "ema_cross":
        required = max(period("ema_fast"), period("ema_slow")) + 2
        filter_history = int(st.get("filter_window") or max(period("ema_fast"), period("ema_slow"), 8))
    elif name == "breakout_donchian":
        required = period("donchian_len") + 2
        filter_history = int(st.get("filter_window") or max(period("donchian_len"), 8))
    else:
        lookback = inspect.signature(es_daily_trend.regime_stability).parameters["lookback_days"].default
        required = max(period("sma_period"), period("atr_period") + int(lookback))
        filter_history = 0
    required = max(required, filter_history)
    before_evaluation = max(int(min_train_bars), int(warmup_bars) + 1)
    if min(row_count, before_evaluation) < required:
        raise ValueError("insufficient_strategy_history")
    return required


def check_research_inputs(rows: list, *, timeframe: str, since_ms: int | None,
                          initial_cash: float, fee_bps: float, slippage_bps: float) -> dict:
    costs = {"initial_cash": initial_cash, "fee_bps": fee_bps, "slippage_bps": slippage_bps}
    for key, value in costs.items():
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"invalid_research_cost:{key}")
    if initial_cash <= 0 or not 0 <= fee_bps < 10000 or not 0 <= slippage_bps < 10000:
        raise ValueError("invalid_research_cost_range")
    match = re.fullmatch(r"([1-9][0-9]*)([smhd])", timeframe)
    if not match:
        raise ValueError("unsupported_research_timeframe")
    step = int(match[1]) * {"s": 1000, "m": 60000, "h": 3600000, "d": 86400000}[match[2]]
    if not rows:
        raise ValueError("research_rows_empty")
    if any(not isinstance(r, (list, tuple)) or len(r) != 6 for r in rows):
        raise ValueError("invalid_research_candle")
    ts = [r[0] for r in rows]
    if any(type(t) is not int or t <= 0 or t % step for t in ts):
        raise ValueError("archive_off_grid")
    if any(b - a != step for a, b in zip(ts, ts[1:])):
        raise ValueError("archive_not_contiguous")
    if since_ms is not None and ts[0] != ((since_ms + step - 1) // step) * step:
        raise ValueError("archive_start_missing")
    for row in rows:
        if len(row) != 6 or any(type(v) not in (int, float) or not math.isfinite(v) for v in row[1:]):
            raise ValueError("invalid_research_candle")
        _, o, h, low, close, volume = row
        if min(o, h, low, close) <= 0 or volume < 0 or not low <= min(o, close) <= max(o, close) <= h:
            raise ValueError("invalid_research_candle")
    return {"status": "passed", "policy": "strict_contiguous_v1", "rows": len(rows),
            "first_ts_ms": ts[0], "last_ts_ms": ts[-1], "cost_assumptions": costs,
            "limitations": ["not_point_in_time_availability_proof", "not_paper_runner_parity",
                            "not_profitability_or_promotion_proof"]}
