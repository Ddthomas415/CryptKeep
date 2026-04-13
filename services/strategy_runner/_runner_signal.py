from __future__ import annotations

from services.risk.exit_controls import evaluate_strategy_exit_stack

import json
import math
import os
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from services.admin.config_editor import load_user_yaml
from services.market_data.multi_venue_view import best_venue
from services.market_data.symbol_router import map_symbol, normalize_symbol, normalize_venue
from services.market_data.tick_reader import get_best_bid_ask_last, mid_price
from services.os.app_paths import ensure_dirs, runtime_dir
from services.risk.market_quality_guard import check as mq_check
from services.security.exchange_factory import make_exchange
from services.strategies.config_tools import build_strategy_block
from services.strategies.presets import get_preset
from services.strategies.strategy_registry import compute_signal
from services.strategies.strategy_selector import select_strategy
from services.risk.exposure_controls import build_risk_limits, summarize_exposure, evaluate_entry
from services.risk.kill_conditions import build_kill_limits, should_block_symbol, evaluate_risk_block_kill
from services.risk.position_scaling import build_scaling_limits, summarize_position_for_scaling, evaluate_scale_in
from services.risk.performance_kill import build_performance_limits, evaluate_exit_outcome, update_drawdown_state, evaluate_performance_kill
from services.validation.paper_multi_symbol_validation import collect_runtime_rows, validate_multi_symbol_state
from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.paper_trading_sqlite import PaperTradingSQLite
from storage.strategy_state_sqlite import StrategyStateSQLite
from services.strategy.startup_guard import require_known_flat_or_override

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
SNAPSHOTS = runtime_dir() / "snapshots"
STOP_FILE = FLAGS / "strategy_runner.stop"
LOCK_FILE = LOCKS / "strategy_runner.lock"
STATUS_FILE = FLAGS / "strategy_runner.status.json"
TICK_SNAPSHOT_FILE = SNAPSHOTS / "system_status.latest.json"

_STRATEGY_ALIASES = {
    "ema_cross": "ema_cross",
    "ema_crossover": "ema_cross",
    "ema_xover": "ema_cross",
    "ema_xover_v1": "ema_cross",
    "mean_reversion": "mean_reversion_rsi",
    "mean_reversion_rsi": "mean_reversion_rsi",
    "breakout": "breakout_donchian",
    "breakout_donchian": "breakout_donchian",
    "donchian": "breakout_donchian",
    "momentum": "momentum",
    "volatility_reversal": "volatility_reversal",
    "gap_fill": "gap_fill",
    "breakout_volume": "breakout_volume",
}
_DEFAULT_PRESET_BY_STRATEGY = {
    "ema_cross": "ema_cross_default",
    "mean_reversion_rsi": "mean_reversion_default",
    "breakout_donchian": "breakout_default",
    "momentum": "momentum_default",
    "volatility_reversal": "volatility_reversal_default",
    "gap_fill": "gap_fill_default",
    "breakout_volume": "breakout_volume_default",
}
_EMA_FIELDS = (
    "ema_fast",
    "ema_slow",
    "filter_window",
    "min_volatility_pct",
    "min_volume_ratio",
    "min_trend_efficiency",
    "min_cross_gap_pct",
)
_MEAN_REVERSION_FIELDS = (
    "rsi_len",
    "rsi_buy",
    "rsi_sell",
    "sma_len",
    "filter_window",
    "max_volatility_pct",
    "min_volume_ratio",
    "max_trend_efficiency",
    "max_sma_distance_pct",
    "require_reversal_confirmation",
)
_BREAKOUT_FIELDS = (
    "donchian_len",
    "filter_window",
    "min_volatility_pct",
    "min_volume_ratio",
    "min_trend_efficiency",
    "min_channel_width_pct",
    "breakout_buffer_pct",
    "require_directional_confirmation",
)

_MOMENTUM_FIELDS = (
    "min_change_pct",
    "max_rsi_entry",
    "rsi_exit",
    "sma_period",
    "rsi_period",
    "stop_below_sma",
)

_VOLATILITY_REVERSAL_FIELDS = (
    "rsi_len",
    "rsi_oversold",
    "rsi_exit",
    "sma_len",
    "min_dump_bars",
    "min_dump_pct",
    "max_volatility_pct",
    "min_volume_ratio",
    "require_volume_spike",
)

_GAP_FILL_FIELDS = (
    "rsi_len",
    "rsi_buy",
    "rsi_sell",
    "sma_len",
    "min_gap_pct",
    "gap_fill_target_pct",
    "min_volume_ratio",
)

_BREAKOUT_VOLUME_FIELDS = (
    "donchian_len",
    "sma_len",
    "filter_window",
    "min_volume_ratio",
    "min_volatility_pct",
    "min_trend_efficiency",
    "breakout_buffer_pct",
    "min_channel_width_pct",
    "require_close_above",
)

def _synth_ohlcv(prices: List[float], *, ts_ms: int | None = None) -> list[list[float]]:
    clean = [float(x) for x in (prices or []) if isinstance(x, (int, float)) and math.isfinite(float(x))]
    if not clean:
        return []
    base_ts = int(ts_ms or int(time.time() * 1000)) - max(0, len(clean) - 1) * 1000
    rows: list[list[float]] = []
    prev = clean[0]
    for idx, close in enumerate(clean):
        open_px = prev if idx else close
        high = max(open_px, close)
        low = min(open_px, close)
        rows.append([base_ts + idx * 1000, open_px, high, low, close, 1.0])
        prev = close
    return rows


def _strategy_signal(cfg: dict, prices: List[float], *, ts_ms: int | None = None) -> dict:
    return compute_signal(
        cfg={"strategy": dict(cfg.get("strategy") or {})},
        symbol=str(cfg.get("symbol") or ""),
        ohlcv=_synth_ohlcv(prices, ts_ms=ts_ms),
    )


def _public_ohlcv_timeframe(cfg: dict) -> str | None:
    source = str(cfg.get("signal_source") or "").strip().lower()
    if source.startswith("public_ohlcv_"):
        timeframe = source.removeprefix("public_ohlcv_").strip()
        return timeframe or None
    return None


def _fetch_public_ohlcv(cfg: dict) -> list[list[float]]:
    timeframe = _public_ohlcv_timeframe(cfg)
    if not timeframe:
        return []
    ex = None
    try:
        ex = make_exchange(cfg["venue"], {"apiKey": None, "secret": None}, enable_rate_limit=True)
        symbol = map_symbol(cfg["venue"], normalize_symbol(cfg["symbol"]))
        limit = max(int(cfg["min_bars"]), int(cfg["max_bars"]))
        rows = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return [list(row) for row in list(rows or []) if isinstance(row, (list, tuple)) and len(row) >= 6]
    except Exception:
        return []
    finally:
        try:
            if ex is not None and hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass

def _fetch_mid(cfg: dict) -> Optional[tuple[float, int]]:
    q = get_best_bid_ask_last(cfg["venue"], cfg["symbol"])
    if q:
        m = mid_price(q)
        ts_ms = int(q.get("ts_ms") or 0)
        if m is None:
            return None
        age = (time.time() * 1000.0 - float(ts_ms)) / 1000.0 if ts_ms else 9999.0
        if age > float(cfg["max_tick_age_sec"]):
            return None
        return float(m), ts_ms
    if not cfg["use_ccxt_fallback"]:
        return None
    ex = None
    try:
        ex = make_exchange(cfg["venue"], {"apiKey": None, "secret": None}, enable_rate_limit=True)
        t = ex.fetch_ticker(cfg["symbol"])
        bid = t.get("bid")
        ask = t.get("ask")
        last = t.get("last")
        if bid is not None and ask is not None:
            m = (float(bid) + float(ask)) / 2.0
        elif last is not None:
            m = float(last)
        else:
            return None
        ts_ms = int(t.get("timestamp") or (time.time() * 1000))
        return m, ts_ms
    except Exception:
        return None
    finally:
        try:
            if ex is not None and hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass


