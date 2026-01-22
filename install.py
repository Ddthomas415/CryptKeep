#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
RUNTIME_DIR = ROOT / "runtime"
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "runtime" / "config"
USER_YAML = CONFIG_DIR / "user.yaml"

def _is_windows() -> bool:
    return platform.system().lower().startswith("win")

def _venv_python() -> Path:
    if _is_windows():
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def _run(cmd: list[str], *, check: bool = True) -> int:
    print(">", " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ROOT))
    if check and p.returncode != 0:
        raise SystemExit(p.returncode)
    return p.returncode

def _ensure_python_version() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        raise SystemExit(f"Python 3.10+ required. You have {major}.{minor}.")

def _ensure_dirs() -> None:
    (RUNTIME_DIR / "flags").mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "locks").mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "snapshots").mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "logs").mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def _write_default_user_yaml_if_missing() -> None:
    if USER_YAML.exists():
        return
    USER_YAML.write_text(
        """# Crypto Bot Pro — user config (safe defaults)
updates:
 enabled: false
 channel_url: ""
 timeout_sec: 5.0
 allow_download: false

meta_strategy:
 enabled: false
 poll_sec: 15
 venue: "binance"
 timeframe: "1h"
 horizon_candles: 6
 internal:
 enabled: true
 weight: 0.6
 ema_fast: 12
 ema_slow: 26
 external:
 enabled: true
 weight: 0.4
 lookback_sec: 21600
 use_reliability: true
 fallback_weight: 0.5
 min_confidence: 0.0
 compose:
 decision_threshold: 0.25
 conflict_hold: true
 conflict_strong_threshold: 0.60
 routing:
 paper_enabled: false
 base_qty: 0.001
 qty_scale_by_score: true
 min_qty_scale: 0.5
 max_qty_scale: 1.5
 cooldown_sec: 300

signals_learning:
 enabled: false
 venue: "binance"
 timeframe: "1h"
 horizon_candles: 6
 min_n_scored: 20
 min_hit_rate: 0.55
 scale_qty: false
 qty_scale_min: 0.5
 qty_scale_max: 1.5

signals:
 auto_route_to_paper: false
 allowed_sources: ["tradingview_alert", "manual_import", "webhook"]
 allowed_authors: []
 allowed_symbols: ["BTC/USDT"]
 default_venue: "binance"
 default_qty: 0.001
 order_type: "market"

preflight:
  venues: ["binance", "coinbase", "gateio"]
  symbols: ["BTC/USDT"]
# Safety defaults (you can edit later in the Dashboard safely)
execution:
  guard_enabled: true
  latency_guard_ms_p95: 2500
  slippage_guard_bps_p95: 25.0
  guard_window_n: 200
  market_data_guard_enabled: true
  market_data_max_age_sec: 5
  spread_guard_enabled: false
  max_spread_bps: 30.0
risk:
  daily_limits_enabled: true
  daily_reset_tz: "UTC"
  max_trades_per_day: 0
  max_daily_notional_usd: 0.0
  max_daily_loss_usd: 0.0
  auto_harvest_pnl_on_evaluate: false
evidence:
  require_consent: true
  allowed_sources: []
  webhook:
    enabled: true
    host: "127.0.0.1"
    port: 8787
    require_hmac: true
    allow_public_bind: false
exchanges:
 binance:
 api_key_env: "BINANCE_API_KEY"
 secret_env: "BINANCE_API_SECRET"
 coinbase:
 api_key_env: "COINBASE_API_KEY"
 secret_env: "COINBASE_API_SECRET"
 gateio:
 api_key_env: "GATEIO_API_KEY"
 secret_env: "GATEIO_API_SECRET"

staleness_guard:
 enabled: true
 max_age_sec: 5.0

live_trading:
 enabled: false
 quote_currency: "USD"
 max_trades_per_day: 3
 max_daily_notional_quote: 250.0
 min_order_notional_quote: 10.0

paper_trading:
intent_consumer:
intent_reconciler:
 enabled: true
 poll_interval_sec: 0.8
 max_intents_per_loop: 50

strategy_runner:
 enabled: true
 strategy_id: "ema_xover_v1"
 venue: "binance"
 symbol: "BTC/USDT"
 auto_select_best_venue: false
 switch_only_when_blocked: true
 venue_candidates: ["binance", "coinbase", "gateio"]
 fast_n: 12
 slow_n: 26
 min_bars: 60
 max_bars: 400
 loop_interval_sec: 1.0
 qty: 0.001
 order_type: "market"
 allow_first_signal_trade: false
 use_ccxt_fallback: true
 max_tick_age_sec: 5.0
 position_aware: true
 sell_full_position: true

 enabled: true
 poll_interval_sec: 0.8
 max_per_loop: 10
 cooldown_sec: 5.0
 cooldown_key: "symbol_side"
 risk_gate_enabled: true
 max_trades_per_day: 0
 max_daily_notional_quote: 0.0

 enabled: true
 quote_currency: "USDT"
 starting_cash_quote: 10000.0
 fee_bps: 7.5
 slippage_bps: 5.0
 default_venue: "binance"
 default_symbol: "BTC/USDT"
 loop_interval_sec: 1.0
 use_ccxt_fallback: true
 max_order_qty: 1000000000.0

market_data_publisher:
  enabled: true
  interval_sec: 2
  write_latest_only: true
  venues: ["binance", "coinbase", "gateio"]
  symbols: ["BTC/USDT"]
  max_symbols_per_venue: 50
""",
        encoding="utf-8",
    )
    print(f"[ok] wrote default config: {USER_YAML}")

def _create_venv() -> None:
    if _venv_python().exists():
        print("[ok] venv exists:", VENV_DIR)
        return
    print("[info] creating venv:", VENV_DIR)
    _run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    print("[ok] venv created")

def _pip_install() -> None:
    py = str(_venv_python())
    _run([py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
    req = ROOT / "requirements.txt"
    pyproj = ROOT / "pyproject.toml"
    if req.exists():
        print("[info] installing requirements.txt")
        _run([py, "-m", "pip", "install", "-r", str(req)], check=True)
        return
    if pyproj.exists():
        print("[info] installing from pyproject.toml (pip install .)")
        _run([py, "-m", "pip", "install", "."], check=True)
        return
    # Fallback minimal deps
    print("[warn] No requirements.txt or pyproject.toml — installing minimal deps.")
    _run([py, "-m", "pip", "install", "streamlit", "ccxt", "pandas", "PyYAML", "keyring"], check=True)

def _print_next_steps() -> None:
    py = _venv_python()
    if _is_windows():
        run_cmd = f'{py} run.py'
        run_cmd2 = f'{py} run.py --tick-publisher'
    else:
        run_cmd = f'{py} run.py'
        run_cmd2 = f'{py} run.py --tick-publisher'
    print("\n[done] install complete.")
    print("Run dashboard:")
    print(" ", run_cmd)
    print("Optional (start tick publisher too):")
    print(" ", run_cmd2)

def main() -> int:
    _ensure_python_version()
    ap = argparse.ArgumentParser(description="Crypto Bot Pro installer (cross-platform).")
    ap.add_argument("--run", action="store_true", help="Run dashboard after install.")
    ap.add_argument("--tick-publisher", action="store_true", help="If --run, also start tick publisher in background.")
    ap.add_argument("--reinstall", action="store_true", help="Force reinstall deps.")
    args = ap.parse_args()
    _ensure_dirs()
    _write_default_user_yaml_if_missing()
    _create_venv()
    if args.reinstall:
        print("[info] forcing reinstall (pip install --upgrade).")
    _pip_install()
    _print_next_steps()
    if args.run:
        py = str(_venv_python())
        cmd = [py, "run.py"]
        if args.tick_publisher:
            cmd.append("--tick-publisher")
        _run(cmd, check=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
watchdog:
  enabled: true
  stale_after_sec: 120
  auto_stop_on_stale: false
  stop_hard: true
  write_crash_snapshot_on_stale: true
alerts:
  enabled: false
  min_level: error
  slack_webhook_url: ""
  rate_limit_sec_default: 60
  never_alert_on_dry_run: true
  rules:
    submit_failed:
      enabled: true
      level: error
      rate_limit_sec: 60
startup_reconciliation:
  enabled: true
  fail_closed_live: true
  fail_closed_paper: false
  lookback_hours: 24
  mark_idempotency_keys: true
  ttl_sec: 86400
  refuse_if_open_orders: true
  require_fresh_for_live: true
  fresh_within_hours: 24
strategy:
  # Available: ema_cross, mean_reversion_rsi, breakout_donchian
  name: ema_cross

  # ema_cross params
  ema_fast: 12
  ema_slow: 26

  # mean_reversion_rsi (disabled by default)
  mr_enabled: false
  mr_rsi_period: 14
  mr_buy_below: 30.0
  mr_sell_above: 70.0

  # breakout_donchian (disabled by default)
  bo_enabled: false
  bo_lookback: 20
live_safety:
  allow_ws_strict: false
execution_intents:
  enabled: true
  max_new_age_sec: 600
strategy:
  # name: ema_cross | mean_reversion_rsi | breakout_donchian
  name: ema_cross
  trade_enabled: true
  # ema_cross
  ema_fast: 12
  ema_slow: 26
  # mean_reversion_rsi
  rsi_len: 14
  rsi_buy: 30.0
  rsi_sell: 70.0
  sma_len: 50
  # breakout_donchian
  donchian_len: 20
execution:
  mode: paper         # paper | live
  venue: binance      # binance | coinbase | gateio
  symbol: "BTC/USDT"  # used by reconciler (optional)
  loop_interval_sec: 2
  reconcile_every_sec: 30
  live_enabled: false # HARD GATE: must be true to allow live orders
# Phase 277 presets: multi-strategy + optional filters
# strategy.type: ema_crossover | mean_reversion | breakout
# strategy.filters are gate-only (no trades created if blocked)
strategy:
  filters:
    volatility:
      enabled: false
      period: 14
      min_atr_pct: 0.08
      max_atr_pct: 6.0
    regime:
      enabled: false
      slow: 50
      slope_lookback: 5
