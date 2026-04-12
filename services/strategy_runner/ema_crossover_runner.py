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
        symbol=symbol,
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


def run_forever() -> None:
    # Runner emission contract:
    # - emits at most one intent per position transition (flat->long, long->exit)
    # - suppresses repeated emissions of the same action via last_emitted_action
    # - latch resets only when the signal/exit condition no longer requests that action
    # - a neutral hold does not force an exit; exits come from opposite signals or explicit exit controls
    # - runner does not own order lifecycle; paper/live engines resolve queued intents
    # - source of truth for current position is PaperTradingSQLite.get_position()
    ensure_dirs()
    cfg = _cfg()
    symbols = list(cfg.get("symbols") or [cfg.get("symbol")])
    symbols = [str(x).strip() for x in symbols if str(x).strip()]
    for symbol in symbols:
        require_known_flat_or_override(venue=cfg["venue"], symbol=symbol)
    if not cfg["enabled"]:
        _write_status({"ok": False, "reason": "disabled", "ts": _now()})
        return
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now()})
        return
    qdb = IntentQueueSQLite()
    pdb = PaperTradingSQLite()
    sdb = StrategyStateSQLite()
    risk_limits = build_risk_limits(cfg)
    kill_limits = build_kill_limits(cfg)
    scaling_limits = build_scaling_limits(cfg)
    performance_limits = build_performance_limits(cfg)

    # Breakout/post-entry exit defaults.
    # These are runner-level controls and should be explicitly versioned in strategy config
    # before governed evidence runs.
    cfg.setdefault("stop_loss_pct", 0.03)
    cfg.setdefault("take_profit_pct", 0.06)
    cfg.setdefault("trailing_stop_pct", 0.02)
    cfg.setdefault("max_bars_hold", 60)

    # ema_cross_v2 post-entry invalidation defaults
    cfg.setdefault("ema_invalidate_on_low_vol", True)
    cfg.setdefault("ema_invalidate_on_chop", True)
    cfg.setdefault("ema_invalidate_on_cross_gap_loss", True)

    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "cfg": cfg, "ts": _now()})
    loops = 0
    enqueued = 0
    try:
        while True:
            loops += 1
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now(), "loops": loops, "enqueued": enqueued})
                break
            # Optional: choose best venue
            if bool(cfg.get("auto_select_best_venue")) and symbols:
                candidates = cfg.get("venue_candidates")
                if not isinstance(candidates, list) or not candidates:
                    # fall back to preflight venues if present
                    base_cfg = load_user_yaml()
                    pf = base_cfg.get("preflight") if isinstance(base_cfg.get("preflight"), dict) else {}
                    candidates = pf.get("venues") if isinstance(pf.get("venues"), list) else [cfg["venue"]]
                candidates = [normalize_venue(str(v)) for v in candidates]
                current_venue = normalize_venue(cfg["venue"])
                cfg["venue"] = current_venue

                probe_symbol = symbols[0]

                if bool(cfg.get("switch_only_when_blocked", True)):
                    g = mq_check(cfg["venue"], probe_symbol)
                    if not g.get("ok"):
                        bv = best_venue(candidates, probe_symbol, require_ok=True)
                        if bv and bv.get("venue") and bv["venue"] != cfg["venue"]:
                            cfg["venue"] = str(bv["venue"])
                else:
                    bv = best_venue(candidates, probe_symbol, require_ok=True)
                    if bv and bv.get("venue"):
                        cfg["venue"] = str(bv["venue"])

            for symbol in symbols:
                signal = {"ok": True, "action": "hold", "reason": "no_signal"}
                selection = {}
                selected_strategy = str(cfg.get("strategy_id") or "ema_cross")

                k_prices = f"prices:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_last_action = f"last_action:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_last_emitted_action = f"last_emitted_action:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_warm = f"warmed:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_entry_price = f"entry_price:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_trailing_peak = f"trailing_peak:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_bars_held = f"bars_held:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_kill_until = f"kill_until:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_risk_block_count = f"risk_block_count:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_scale_count = f"scale_count:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_loss_streak = f"loss_streak:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_cum_pnl = f"cum_pnl:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"
                k_peak_pnl = f"peak_pnl:{cfg['venue']}:{symbol}:{cfg['strategy_id']}"

                try:
                    prices = json.loads(sdb.get(k_prices) or "[]")
                    if not isinstance(prices, list):
                        prices = []
                    prices = [float(x) for x in prices if isinstance(x, (int, float)) and math.isfinite(float(x))]
                except Exception:
                    prices = []

                warmed = (sdb.get(k_warm) or "") == "1"
                last_action = str(sdb.get(k_last_action) or "hold").strip().lower()
                if last_action not in ("buy", "sell", "hold"):
                    last_action = "hold"
                last_emitted_action = str(sdb.get(k_last_emitted_action) or "hold").strip().lower()
                if last_emitted_action not in ("buy", "sell", "hold"):
                    last_emitted_action = "hold"

                sym_cfg = dict(cfg)
                sym_cfg["symbol"] = symbol

                timeframe = _public_ohlcv_timeframe(sym_cfg)
                if timeframe:
                    ohlcv = _fetch_public_ohlcv(sym_cfg) or []
                    if not ohlcv:
                        _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now(), "note": "no_public_ohlcv", "loops": loops, "enqueued": enqueued})
                        time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                        continue
                    prices = [float(row[4]) for row in ohlcv[-int(cfg["max_bars"]):]]
                    if loops % 5 == 0:
                        sdb.set(k_prices, json.dumps(prices))
                    if len(ohlcv) < int(cfg["min_bars"]):
                        _write_status(
                            {
                                "ok": True,
                                "status": "running",
                                "pid": os.getpid(),
                                "ts": _now(),
                                "mid": float(ohlcv[-1][4]),
                                "bars": len(ohlcv),
                                "note": "warming",
                                "enqueued": enqueued,
                                "strategy_id": cfg["strategy_id"],
                                "strategy_source": cfg["signal_source"],
                            }
                        )
                        time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                        continue
                    ts_ms = int(ohlcv[-1][0] or (time.time() * 1000))
                    m = float(ohlcv[-1][4])
                    selection = select_strategy(
                        default_strategy=str(cfg.get("strategy_id") or "ema_cross"),
                        ohlcv=ohlcv[-int(cfg["min_bars"]):],
                    )
                    selected_strategy = str(selection.get("selected_strategy") or cfg.get("strategy_id") or "ema_cross")
                    signal = compute_signal(
                        cfg={"strategy": {**dict(cfg.get("strategy") or {}), "name": selected_strategy}},
                        symbol=symbol,
                        ohlcv=ohlcv[-int(cfg["min_bars"]):],
                    )
                    bars = len(ohlcv)
                else:
                    tick = _fetch_mid(sym_cfg)
                    if not tick:
                        _write_status(
                            {
                                "ok": True,
                                "status": "running",
                                "pid": os.getpid(),
                                "ts": _now(),
                                "note": _no_fresh_tick_note(),
                                "loops": loops,
                                "enqueued": enqueued,
                            }
                        )
                        time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                        continue
                    m, ts_ms = tick
                    prices.append(float(m))
                    if len(prices) > int(cfg["max_bars"]):
                        prices = prices[-int(cfg["max_bars"]):]
                    if loops % 5 == 0:
                        sdb.set(k_prices, json.dumps(prices))
                    if len(prices) < int(cfg["min_bars"]):
                        _write_status(
                            {
                                "ok": True,
                                "status": "running",
                                "pid": os.getpid(),
                                "ts": _now(),
                                "mid": m,
                                "bars": len(prices),
                                "note": "warming",
                                "enqueued": enqueued,
                                "strategy_id": cfg["strategy_id"],
                            "strategy_source": cfg["signal_source"],
                        }
                    )
                    time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
                    continue
                selection = select_strategy(
                    default_strategy=str(cfg.get("strategy_id") or "ema_cross"),
                    ohlcv=_synth_ohlcv(prices[-int(cfg["min_bars"]):], ts_ms=ts_ms),
                )
                selected_strategy = str(selection.get("selected_strategy") or cfg.get("strategy_id") or "ema_cross")
                signal = compute_signal(
                    cfg={"strategy": {**dict(cfg.get("strategy") or {}), "name": selected_strategy}},
                    symbol=symbol,
                    ohlcv=_synth_ohlcv(prices[-int(cfg["min_bars"]):], ts_ms=ts_ms),
                )
                bars = len(prices)
            decision = str(signal.get("action") or "hold").lower().strip()
            if decision not in ("buy", "sell", "hold"):
                decision = "hold"
            changed = False
            note = None
            if not warmed:
                if decision in ("buy", "sell") and bool(cfg["allow_first_signal_trade"]):
                    changed = True
                sdb.set(k_last_action, decision)
                sdb.set(k_warm, "1")
                warmed = True
                last_action = decision
                note = "warmed_no_trade"
            else:
                changed = decision != last_action
                if changed:
                    last_action = decision
                    sdb.set(k_last_action, decision)
            action = None
            pos = pdb.get_position(symbol) or {"qty": 0.0, "avg_price": 0.0}
            scale_count = int(str(sdb.get(k_scale_count) or "0").strip() or 0)

            all_positions = []
            try:
                if hasattr(pdb, "list_positions"):
                    all_positions = list(pdb.list_positions() or [])
                elif hasattr(pdb, "get_all_positions"):
                    all_positions = list(pdb.get_all_positions() or [])
                elif hasattr(pdb, "positions"):
                    all_positions = list(pdb.positions() or [])
            except Exception:
                all_positions = []

            all_positions, all_intents = collect_runtime_rows(
                paper_db=pdb,
                intent_db=qdb,
            )

            exposure = summarize_exposure(
                positions=all_positions,
                strategy_name=str(cfg.get("strategy_id") or ""),
            )

            multi_symbol_validation = validate_multi_symbol_state(
                positions=all_positions,
                intents=all_intents,
                max_open_intents_per_symbol=int(risk_limits.get("max_open_intents_per_symbol", 1)),
            )
            pos_qty = float(pos.get("qty") or 0.0)

            # Track entry/hold state for strategy-aware exit controls.
            entry_price = float(sdb.get(k_entry_price) or 0.0)
            trailing_peak_price = float(sdb.get(k_trailing_peak) or 0.0)
            bars_held = int(sdb.get(k_bars_held) or 0)

            if pos_qty <= 0.0:
                # No open position: clear runner-side exit state.
                for k in (k_entry_price, k_trailing_peak, k_bars_held):
                    try:
                        sdb.delete(k)
                    except Exception:
                        pass
                entry_price = 0.0
                trailing_peak_price = 0.0
                bars_held = 0
            else:
                # Seed entry state from live paper position if missing.
                if entry_price <= 0.0:
                    avg_price = float(pos.get("avg_price") or 0.0)
                    if avg_price > 0.0:
                        entry_price = avg_price
                        sdb.set(k_entry_price, str(entry_price))
                bars_held += 1
                sdb.set(k_bars_held, str(bars_held))

                cur_px = float(m)
                if cur_px > 0.0:
                    trailing_peak_price = max(float(trailing_peak_price or 0.0), cur_px)
                    sdb.set(k_trailing_peak, str(trailing_peak_price))

            # Strategy-aware exit stack takes priority over signal-change actioning.
            exit_action = None
            exit_reason = None
            exit_out = {}

            # ema_cross_v2: invalidate open long if the original setup degrades into
            # low-vol / chop / collapsed cross-gap after entry.
            sig_ind = signal.get("ind") or {}
            if (
                pos_qty > 0.0
                and entry_price > 0.0
                and str(cfg.get("strategy_id")) == "ema_cross"
            ):
                avg_range_pct = float(sig_ind.get("avg_range_pct") or 0.0)
                trend_eff = float(sig_ind.get("trend_efficiency") or 0.0)
                cross_gap_pct = float(sig_ind.get("cross_gap_pct") or 0.0)

                min_vol = float(cfg.get("min_volatility_pct", 0.0) or 0.0)
                min_trend = float(cfg.get("min_trend_efficiency", 0.0) or 0.0)
                min_gap = float(cfg.get("min_cross_gap_pct", 0.0) or 0.0)

                if bool(cfg.get("ema_invalidate_on_low_vol", True)) and avg_range_pct < min_vol:
                    exit_action = "sell"
                    exit_reason = "strategy_exit:ema_cross:low_volatility_invalidation"
                elif bool(cfg.get("ema_invalidate_on_chop", True)) and trend_eff < min_trend:
                    exit_action = "sell"
                    exit_reason = "strategy_exit:ema_cross:chop_invalidation"
                elif bool(cfg.get("ema_invalidate_on_cross_gap_loss", True)) and cross_gap_pct < min_gap:
                    exit_action = "sell"
                    exit_reason = "strategy_exit:ema_cross:cross_gap_invalidation"

            if pos_qty > 0.0 and entry_price > 0.0 and not exit_action:
                exit_out = evaluate_strategy_exit_stack(
                    entry_price=entry_price,
                    current_price=float(m),
                    qty=float(pos_qty),
                    side="long",
                    strategy=str(cfg["strategy_id"]),
                    stop_loss_pct=float(cfg.get("stop_loss_pct", 0.0) or 0.0),
                    take_profit_pct=float(cfg.get("take_profit_pct", 0.0) or 0.0),
                    trailing_peak_price=float(trailing_peak_price or 0.0) if trailing_peak_price > 0.0 else None,
                    trailing_stop_pct=float(cfg.get("trailing_stop_pct", 0.0) or 0.0),
                    bars_held=int(bars_held),
                    max_bars_hold=int(cfg.get("max_bars_hold", 0) or 0) or None,
                )
                if str(exit_out.get("action") or "") == "exit":
                    exit_action = "sell"
                    exit_reason = str(exit_out.get("reason") or exit_out.get("stack_rule") or "strategy_exit")

            if exit_action:
                action = "sell"
                note = exit_reason
                changed = False
            elif changed:
                if decision == "buy":
                    if (not cfg["position_aware"]) or (pos_qty <= 0.0):
                        action = "buy"
                elif decision == "sell":
                    if (not cfg["position_aware"]) or (pos_qty > 0.0):
                        action = "sell"
            kill_until_loop = int(str(sdb.get(k_kill_until) or "0").strip() or 0)
            kill_gate = should_block_symbol(loops=loops, kill_until_loop=kill_until_loop)
            if not bool(kill_gate.get("ok")):
                _write_status(
                    {
                        "ok": True,
                        "status": "running",
                        "pid": os.getpid(),
                        "ts": _now(),
                        "venue": cfg["venue"],
                        "symbol": symbol,
                        "symbols": symbols,
                        "strategy_id": cfg.get("strategy_id"),
                        "note": "kill_cooldown",
                        "kill_reason": kill_gate.get("reason"),
                        "kill_remaining_loops": kill_gate.get("remaining_loops"),
                    }
                )
                continue

            if action and action == last_emitted_action:
                action = None
            if action:
                intent_id = str(uuid.uuid4())
                qty = float(cfg["qty"])
                if action == "sell" and bool(cfg["sell_full_position"]) and pos_qty > 0.0:
                    qty = pos_qty

                # Keep exit-state in sync with newly emitted intents.
                if action == "buy":
                    position_summary = summarize_position_for_scaling(pos, float(m))
                    scale_check = evaluate_scale_in(
                        position_summary=position_summary,
                        adds_used=scale_count,
                        limits=scaling_limits,
                    )
                    if bool(scale_check.get("is_scale")) and not bool(scale_check.get("ok")):
                        _write_status(
                            {
                                "ok": True,
                                "status": "running",
                                "pid": os.getpid(),
                                "ts": _now(),
                                "venue": cfg["venue"],
                                "symbol": symbol,
                                "symbols": symbols,
                                "strategy_id": cfg.get("strategy_id"),
                                "signal_action": action,
                                "signal_reason": signal.get("reason") if isinstance(signal, dict) else None,
                                "scale_reason": scale_check.get("reason"),
                                "scale_count": scale_count,
                                "position_summary": position_summary,
                                "note": "scale_blocked_entry",
                            }
                        )
                        continue

                    risk_check = evaluate_entry(
                        symbol=symbol,
                        strategy_name=str(cfg.get("strategy_id") or ""),
                        limits=risk_limits,
                        exposure=exposure,
                        open_intents_for_symbol=0,
                    )
                    if not bool(risk_check.get("ok")):
                        risk_block_count = int(str(sdb.get(k_risk_block_count) or "0").strip() or 0) + 1
                        sdb.set(k_risk_block_count, str(risk_block_count))

                        kill_eval = evaluate_risk_block_kill(
                            loops=loops,
                            consecutive_risk_blocks=risk_block_count,
                            limits=kill_limits,
                        )
                        if bool(kill_eval.get("triggered")):
                            sdb.set(k_kill_until, str(int(kill_eval.get("kill_until_loop", 0))))
                            _write_status(
                                {
                                    "ok": True,
                                    "status": "running",
                                    "pid": os.getpid(),
                                    "ts": _now(),
                                    "venue": cfg["venue"],
                                    "symbol": symbol,
                                    "symbols": symbols,
                                    "strategy_id": cfg.get("strategy_id"),
                                    "signal_action": action,
                                    "signal_reason": signal.get("reason") if isinstance(signal, dict) else None,
                                    "risk_reason": risk_check.get("reason"),
                                    "risk_exposure": exposure,
                                    "paper_validation": multi_symbol_validation,
                                    "risk_block_count": risk_block_count,
                                    "kill_reason": kill_eval.get("reason"),
                                    "kill_until_loop": kill_eval.get("kill_until_loop"),
                                    "note": "kill_triggered_risk_blocks",
                                }
                            )
                        else:
                            _write_status(
                                {
                                    "ok": True,
                                    "status": "running",
                                    "pid": os.getpid(),
                                    "ts": _now(),
                                    "venue": cfg["venue"],
                                    "symbol": symbol,
                                    "symbols": symbols,
                                    "strategy_id": cfg.get("strategy_id"),
                                    "signal_action": action,
                                    "signal_reason": signal.get("reason") if isinstance(signal, dict) else None,
                                    "risk_reason": risk_check.get("reason"),
                                    "risk_exposure": exposure,
                                    "paper_validation": multi_symbol_validation,
                                    "risk_block_count": risk_block_count,
                                    "note": "risk_blocked_entry",
                                }
                            )
                        continue

                    sdb.set(k_risk_block_count, "0")
                    sdb.set(k_kill_until, "0")
                    if bool(position_summary.get("has_position")):
                        sdb.set(k_scale_count, str(scale_count + 1))
                    sdb.set(k_entry_price, str(float(m)))
                    sdb.set(k_trailing_peak, str(float(m)))
                    sdb.set(k_bars_held, "0")
                elif action == "sell":
                    entry_price_val = float(str(sdb.get(k_entry_price) or "0").strip() or 0.0)
                    exit_eval = evaluate_exit_outcome(
                        entry_price=entry_price_val,
                        exit_price=float(m),
                    )
                    if bool(exit_eval.get("ok")):
                        prior_cum = float(str(sdb.get(k_cum_pnl) or "0").strip() or 0.0)
                        prior_peak = float(str(sdb.get(k_peak_pnl) or "0").strip() or 0.0)
                        dd_state = update_drawdown_state(
                            cumulative_pnl_pct=prior_cum,
                            peak_pnl_pct=prior_peak,
                            trade_pnl_pct=float(exit_eval.get("pnl_pct", 0.0)),
                        )
                        sdb.set(k_cum_pnl, str(dd_state["cumulative_pnl_pct"]))
                        sdb.set(k_peak_pnl, str(dd_state["peak_pnl_pct"]))

                        loss_streak = int(str(sdb.get(k_loss_streak) or "0").strip() or 0)
                        loss_streak = (loss_streak + 1) if bool(exit_eval.get("is_loss")) else 0
                        sdb.set(k_loss_streak, str(loss_streak))

                        perf_kill = evaluate_performance_kill(
                            loops=loops,
                            consecutive_losing_exits=loss_streak,
                            drawdown_pct=float(dd_state.get("drawdown_pct", 0.0)),
                            limits=performance_limits,
                        )
                        if bool(perf_kill.get("triggered")):
                            sdb.set(k_kill_until, str(int(perf_kill.get("kill_until_loop", 0))))
                            _write_status(
                                {
                                    "ok": True,
                                    "status": "running",
                                    "pid": os.getpid(),
                                    "ts": _now(),
                                    "venue": cfg["venue"],
                                    "symbol": symbol,
                                    "symbols": symbols,
                                    "strategy_id": cfg.get("strategy_id"),
                                    "signal_action": action,
                                    "signal_reason": signal.get("reason") if isinstance(signal, dict) else None,
                                    "performance_exit": exit_eval,
                                    "performance_state": dd_state,
                                    "loss_streak": loss_streak,
                                    "kill_reason": perf_kill.get("reason"),
                                    "kill_until_loop": perf_kill.get("kill_until_loop"),
                                    "note": "kill_triggered_performance",
                                }
                            )
                    for k in (k_entry_price, k_trailing_peak, k_bars_held):
                        try:
                            sdb.delete(k)
                        except Exception:
                            pass

                qdb.upsert_intent({
                    "intent_id": intent_id,
                    "created_ts": _now(),
                    "ts": _now(),
                    "source": "strategy",
                    "strategy_id": cfg["strategy_id"],
                    "venue": cfg["venue"],
                    "symbol": symbol,
                    "side": action,
                    "order_type": cfg["order_type"],
                    "qty": float(qty),
                    "limit_price": None,
                    "status": "queued",
                    "last_error": None,
                    "client_order_id": None,
                    "linked_order_id": None,
                    "meta": {
                        "selected_strategy": selected_strategy if 'selected_strategy' in locals() else cfg["strategy_id"],
                        "selected_strategy_reason": selection.get("selected_strategy_reason") if 'selection' in locals() and isinstance(selection, dict) else None,
                        "regime": selection.get("regime") if 'selection' in locals() and isinstance(selection, dict) else None,
                        "volume_surge": selection.get("volume_surge") if 'selection' in locals() and isinstance(selection, dict) else None,
                        "volume_ratio": selection.get("volume_ratio") if 'selection' in locals() and isinstance(selection, dict) else None,
                        "signal_reason": signal.get("reason") if isinstance(signal, dict) else None,
                        "ranked_candidates": selection.get("ranked_candidates") if 'selection' in locals() and isinstance(selection, dict) else None,
                        "candidate_scores": selection.get("candidate_scores") if 'selection' in locals() and isinstance(selection, dict) else None,
                    },
                })
                enqueued += 1
                last_emitted_action = action
                sdb.set(k_last_emitted_action, last_emitted_action)
            elif not exit_action and decision == "hold" and last_emitted_action != "hold":
                last_emitted_action = "hold"
                sdb.set(k_last_emitted_action, last_emitted_action)
            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now(),
                "loops": loops,
                "enqueued_total": enqueued,
                "mid": m if 'm' in locals() else None,
                "ts_ms": ts_ms if 'ts_ms' in locals() else None,
                "bars": bars if 'bars' in locals() else len(prices),
                "strategy_id": cfg["strategy_id"] if 'cfg' in locals() else None,
                "selected_strategy": selected_strategy if 'selected_strategy' in locals() else None,
                "selected_strategy_reason": selection.get("selected_strategy_reason") if 'selection' in locals() and isinstance(selection, dict) else None,
                "regime": selection.get("regime") if 'selection' in locals() and isinstance(selection, dict) else None,
                "volume_surge": selection.get("volume_surge") if 'selection' in locals() and isinstance(selection, dict) else None,
                "volume_ratio": selection.get("volume_ratio") if 'selection' in locals() and isinstance(selection, dict) else None,
                "strategy_preset": cfg["strategy_preset"] if 'cfg' in locals() else None,
                "signal_source": cfg["signal_source"] if 'cfg' in locals() else None,
                "signal_action": decision if 'decision' in locals() else None,
                "signal_reason": signal.get("reason") if 'signal' in locals() and isinstance(signal, dict) else None,
                "symbols": symbols,
                "symbol": symbol,
                "signal_ok": bool(signal.get("ok", False)) if 'signal' in locals() and isinstance(signal, dict) else None,
                "signal_changed": bool(changed) if 'changed' in locals() else None,
                "signal_indicators": signal.get("ind") if 'signal' in locals() and isinstance(signal, dict) else None,
                "pos_qty": pos_qty if 'pos_qty' in locals() else None,
                "entry_price": entry_price if 'entry_price' in locals() else None,
                "trailing_peak_price": trailing_peak_price if 'trailing_peak_price' in locals() else None,
                "bars_held": bars_held if 'bars_held' in locals() else None,
                "exit_action": exit_action if 'exit_action' in locals() else None,
                "exit_reason": exit_reason if 'exit_reason' in locals() else None,
                "exit_stack_rule": exit_out.get("stack_rule") if 'exit_out' in locals() and isinstance(exit_out, dict) else None,
                "exit_stack_action": exit_out.get("action") if 'exit_out' in locals() and isinstance(exit_out, dict) else None,
                "action": action if 'action' in locals() else None,
                "note": note if 'note' in locals() else None,
            })
            time.sleep(max(0.2, float(cfg["loop_interval_sec"])))
    finally:
        try:
            sdb.set(k_prices, json.dumps(prices))
            sdb.set(k_last_action, last_action)
            sdb.set(k_last_emitted_action, last_emitted_action)
        except Exception:
            pass
        _release_lock()
        _write_status({
            "ok": True,
            "status": "stopped",
            "pid": os.getpid(),
            "ts": _now(),
            "loops": loops,
            "enqueued_total": enqueued,
            "mid": m if 'm' in locals() else None,
            "ts_ms": ts_ms if 'ts_ms' in locals() else None,
            "bars": bars if 'bars' in locals() else len(prices),
            "strategy_id": cfg["strategy_id"] if 'cfg' in locals() else None,
            "strategy_preset": cfg["strategy_preset"] if 'cfg' in locals() else None,
            "signal_source": cfg["signal_source"] if 'cfg' in locals() else None,
            "signal_action": decision if 'decision' in locals() else None,
            "signal_reason": signal.get("reason") if 'signal' in locals() and isinstance(signal, dict) else None,
            "signal_ok": bool(signal.get("ok", False)) if 'signal' in locals() and isinstance(signal, dict) else None,
            "signal_changed": bool(changed) if 'changed' in locals() else None,
            "signal_indicators": signal.get("ind") if 'signal' in locals() and isinstance(signal, dict) else None,
            "pos_qty": pos_qty if 'pos_qty' in locals() else None,
            "entry_price": entry_price if 'entry_price' in locals() else None,
            "trailing_peak_price": trailing_peak_price if 'trailing_peak_price' in locals() else None,
            "bars_held": bars_held if 'bars_held' in locals() else None,
            "exit_action": exit_action if 'exit_action' in locals() else None,
            "exit_reason": exit_reason if 'exit_reason' in locals() else None,
            "exit_stack_rule": exit_out.get("stack_rule") if 'exit_out' in locals() and isinstance(exit_out, dict) else None,
            "exit_stack_action": exit_out.get("action") if 'exit_out' in locals() and isinstance(exit_out, dict) else None,
            "action": action if 'action' in locals() else None,
            "note": note if 'note' in locals() else None,
        })


# ---- runtime defaults (override by env set from scripts/bot_ctl.py) ----
DEFAULT_SYMBOL = "BTC/USD"
