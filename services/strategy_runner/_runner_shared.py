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

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _no_fresh_tick_note(*, stale_after_sec: float = 30.0) -> str:
    if not TICK_SNAPSHOT_FILE.exists():
        return "no_fresh_tick:snapshot_file_missing:start_tick_publisher"
    try:
        age_sec = max(0.0, time.time() - float(TICK_SNAPSHOT_FILE.stat().st_mtime))
    except Exception:
        age_sec = stale_after_sec + 1.0
    if age_sec > float(stale_after_sec):
        return "no_fresh_tick:snapshot_stale:publisher_stopped_or_network_blocked"
    try:
        snap = json.loads(TICK_SNAPSHOT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return "no_fresh_tick:snapshot_unreadable:check_tick_publisher_output"
    ticks = snap.get("ticks")
    if not isinstance(ticks, list) or not ticks:
        return "no_fresh_tick:snapshot_has_no_ticks:check_venue_connectivity"
    return "no_fresh_tick:snapshot_present_but_symbol_missing:check_symbol_or_venue_mapping"

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        return False
    LOCK_FILE.write_text(json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n", encoding="utf-8")
    return True

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}

def _cfg() -> dict:
    cfg = load_user_yaml()
    s = cfg.get("strategy_runner") if isinstance(cfg.get("strategy_runner"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}

    default_symbol = globals().get("DEFAULT_SYMBOL", "BTC/USD")
    pf_venues = pf.get("venues") if isinstance(pf.get("venues"), list) else []
    pf_symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else []

    env_v = (os.environ.get("CBP_VENUE") or "").strip().lower()
    venue = str(env_v or s.get("venue") or (pf_venues[0] if pf_venues else "coinbase")).lower().strip()

    env_syms = [x.strip() for x in (os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()]
    cfg_symbols = s.get("symbols") if isinstance(s.get("symbols"), list) else []
    symbols = (
        env_syms
        or [x for x in cfg_symbols if str(x).strip()]
        or [x for x in pf_symbols if str(x).strip()]
        or [str(s.get("symbol") or default_symbol).strip()]
    )
    symbols = [str(x).strip() for x in symbols if str(x).strip()]
    symbol = str(symbols[0] if symbols else default_symbol).strip()
    strategy_block, strategy_preset = _strategy_block_from_runner_cfg(s)
    env_min_bars_raw = str(os.environ.get("CBP_STRATEGY_MIN_BARS") or "").strip()
    env_min_bars = int(env_min_bars_raw) if env_min_bars_raw else 0
    min_bars_source = env_min_bars if env_min_bars > 0 else int(s.get("min_bars", 60) or 60)
    min_bars = max(int(min_bars_source), _required_history(strategy_block))
    allow_first_signal_trade = bool(s.get("allow_first_signal_trade", False))
    if str(os.environ.get("CBP_STRATEGY_ALLOW_FIRST_SIGNAL_TRADE", "")).strip().lower() in {"1", "true", "yes", "on"}:
        allow_first_signal_trade = True
    signal_source = str(
        os.environ.get("CBP_STRATEGY_SIGNAL_SOURCE")
        or s.get("signal_source")
        or "synthetic_mid_ohlcv"
    ).strip().lower() or "synthetic_mid_ohlcv"
    venue_candidates = s.get("venue_candidates") if isinstance(s.get("venue_candidates"), list) else []

    return {
        "enabled": bool(s.get("enabled", True)),
        "strategy_id": str(strategy_block["name"]),
        "strategy": strategy_block,
        "strategy_preset": str(strategy_preset),
        "venue": venue,
        "symbol": symbol,
        "symbols": symbols,
        "fast_n": int(s.get("fast_n", 12) or 12),
        "slow_n": int(s.get("slow_n", 26) or 26),
        "min_bars": int(min_bars),
        "max_bars": int(s.get("max_bars", 400) or 400),
        "loop_interval_sec": float(s.get("loop_interval_sec", 1.0) or 1.0),
        "qty": float(s.get("qty", 0.001) or 0.001),
        "order_type": str(s.get("order_type", "market") or "market").lower().strip(),
        "allow_first_signal_trade": allow_first_signal_trade,
        "use_ccxt_fallback": bool(s.get("use_ccxt_fallback", True)),
        "max_tick_age_sec": float(s.get("max_tick_age_sec", 5.0) or 5.0),
        "position_aware": bool(s.get("position_aware", True)),
        "sell_full_position": bool(s.get("sell_full_position", True)),
        "signal_source": signal_source,
        "auto_select_best_venue": bool(s.get("auto_select_best_venue", False)),
        "switch_only_when_blocked": bool(s.get("switch_only_when_blocked", True)),
        "venue_candidates": [str(v).lower().strip() for v in venue_candidates if str(v).strip()],
    }


def _canonical_strategy_name(raw: object) -> str:
    key = str(raw or "").strip().lower()
    return _STRATEGY_ALIASES.get(key, "ema_cross")


def _legacy_strategy_params(s: dict, strategy_name: str) -> dict:
    params: dict = {}
    if strategy_name == "ema_cross":
        if "fast_n" in s:
            params["ema_fast"] = s.get("fast_n")
        if "slow_n" in s:
            params["ema_slow"] = s.get("slow_n")
        for field in _EMA_FIELDS[2:]:
            if field in s:
                params[field] = s.get(field)
        return params
    if strategy_name == "mean_reversion_rsi":
        for field in _MEAN_REVERSION_FIELDS:
            if field in s:
                params[field] = s.get(field)
        return params
    if strategy_name == "breakout_donchian":
        for field in _BREAKOUT_FIELDS:
            if field in s:
                params[field] = s.get(field)
        return params
    if strategy_name == "momentum":
        for field in _MOMENTUM_FIELDS:
            if field in s:
                params[field] = s.get(field)
        return params
    if strategy_name == "volatility_reversal":
        for field in _VOLATILITY_REVERSAL_FIELDS:
            if field in s:
                params[field] = s.get(field)
        return params
    if strategy_name == "gap_fill":
        for field in _GAP_FILL_FIELDS:
            if field in s:
                params[field] = s.get(field)
        return params
    if strategy_name == "breakout_volume":
        for field in _BREAKOUT_VOLUME_FIELDS:
            if field in s:
                params[field] = s.get(field)
        return params
    return params


def _strategy_block_from_runner_cfg(s: dict) -> tuple[dict, str]:
    nested = s.get("strategy") if isinstance(s.get("strategy"), dict) else {}
    raw_name = (
        os.environ.get("CBP_STRATEGY_NAME")
        or nested.get("name")
        or s.get("strategy_name")
        or s.get("strategy_id")
        or "ema_cross"
    )
    strategy_name = _canonical_strategy_name(raw_name)
    default_preset = _DEFAULT_PRESET_BY_STRATEGY[strategy_name]
    preset_name = str(
        os.environ.get("CBP_STRATEGY_PRESET")
        or s.get("strategy_preset")
        or default_preset
    ).strip() or default_preset
    preset = get_preset(preset_name) or get_preset(default_preset) or {}
    if preset_name != default_preset and not get_preset(preset_name):
        preset_name = default_preset

    merged = dict(preset.get("strategy") if isinstance(preset.get("strategy"), dict) else {})
    merged.update(_legacy_strategy_params(s, strategy_name))
    for key, value in nested.items():
        if key == "name" or value is None:
            continue
        merged[key] = value

    trade_enabled = bool(nested.get("trade_enabled", merged.get("trade_enabled", True)))
    strategy_block = build_strategy_block(
        name=strategy_name,
        trade_enabled=trade_enabled,
        params=merged,
    )
    return strategy_block, preset_name


def _required_history(strategy_block: dict) -> int:
    name = str(strategy_block.get("name") or "ema_cross")
    if name == "ema_cross":
        return max(
            int(strategy_block.get("ema_slow", 26) or 26) + 2,
            int(strategy_block.get("filter_window", 0) or 0) + 2,
            5,
        )
    if name == "mean_reversion_rsi":
        return max(
            int(strategy_block.get("rsi_len", 14) or 14) + 2,
            int(strategy_block.get("sma_len", 50) or 50) + 2,
            int(strategy_block.get("filter_window", 0) or 0) + 2,
            5,
        )
    if name == "breakout_donchian":
        return max(
            int(strategy_block.get("donchian_len", 20) or 20) + 2,
            int(strategy_block.get("filter_window", 0) or 0) + 2,
            5,
        )
    return 5


