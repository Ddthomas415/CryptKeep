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

from services.strategy_runner._runner_shared import (
    _now,
    _write_status,
    _no_fresh_tick_note,
    _acquire_lock,
    _release_lock,
    _cfg,
)
from services.strategy_runner._runner_signal import (
    _public_ohlcv_timeframe,
    _fetch_public_ohlcv,
    _fetch_mid,
)

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
                                "strategy_id": selected_strategy if 'selected_strategy' in locals() else cfg["strategy_id"],
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
                    raw_cfg = load_user_yaml()
                    raw_runner = raw_cfg.get("strategy_runner") if isinstance(raw_cfg.get("strategy_runner"), dict) else {}
                    raw_strategy = raw_runner.get("strategy") if isinstance(raw_runner.get("strategy"), dict) else {}

                    selected_params = dict(raw_strategy)
                    selected_params.pop("name", None)
                    selected_params.pop("trade_enabled", None)

                    selected_block = build_strategy_block(
                        name=selected_strategy,
                        trade_enabled=bool(raw_strategy.get("trade_enabled", True)),
                        params=selected_params,
                    )
                    signal = compute_signal(
                        cfg={"strategy": selected_block},
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

                open_strategy_intent_exists = False
                try:
                    for row in qdb.list_intents(limit=200):
                        if (
                            row.get("source") == "strategy"
                            and row.get("symbol") == symbol
                            and row.get("status") in ("queued", "submitted")
                        ):
                            open_strategy_intent_exists = True
                            break
                except Exception:
                    open_strategy_intent_exists = False

                if open_strategy_intent_exists:
                    _write_status({
                        "ok": True,
                        "status": "running",
                        "pid": os.getpid(),
                        "ts": _now(),
                        "loops": loops,
                        "enqueued_total": enqueued,
                        "mid": m if 'm' in locals() else None,
                        "venue": cfg["venue"],
                        "symbol": symbol,
                        "symbols": symbols,
                        "strategy_id": cfg.get("strategy_id"),
                        "selected_strategy": selected_strategy if 'selected_strategy' in locals() else cfg.get("strategy_id"),
                        "selected_strategy_reason": selection.get("selected_strategy_reason") if 'selection' in locals() and isinstance(selection, dict) else None,
                        "regime": selection.get("regime") if 'selection' in locals() and isinstance(selection, dict) else None,
                        "signal_ok": signal.get("ok") if isinstance(signal, dict) else None,
                        "signal_action": action,
                        "signal_reason": signal.get("reason") if isinstance(signal, dict) else None,
                        "signal_changed": signal_changed,
                        "note": "open_strategy_intent_exists",
                    })
                else:
                    qdb.upsert_intent({
                        "intent_id": intent_id,
                        "created_ts": _now(),
                        "ts": _now(),
                        "source": "strategy",
                        "strategy_id": selected_strategy if 'selected_strategy' in locals() else cfg["strategy_id"],
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
