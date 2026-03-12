from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st
from dashboard.auth_gate import require_authenticated_role
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.admin.repair_wizard import CONFIRM_TEXT as REPAIR_CONFIRM_TEXT
from services.admin.repair_wizard import execute_reset, preflight_self_check, preview_reset
from services.app.preflight_wizard import render_guided_setup_panel
from services.backtest.parity_engine import run_parity_backtest
from services.execution.idempotency_inspector import filter_rows as filter_idem_rows
from services.execution.idempotency_inspector import list_recent as list_idem_recent
from services.strategies.config_tools import (
    apply_preset_and_validate,
    apply_strategy_block,
    build_strategy_block,
    supported_strategies,
    validate_cfg,
)
from services.strategies.presets import list_presets

_st_button = st.button


def _disabled_button(label: str, *args, **kwargs):
    if isinstance(label, str) and "Start Live Bot" in label:
        kwargs["disabled"] = True
        return False
    return _st_button(label, *args, **kwargs)


st.button = _disabled_button

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDED_SETUP_PRESETS = ["safe_paper", "paper_relaxed", "live_locked"]


def _guided_preset_label(preset: str) -> str:
    labels = {
        "safe_paper": "safe_paper (recommended)",
        "paper_relaxed": "paper_relaxed",
        "live_locked": "live_locked",
    }
    return labels.get(str(preset), str(preset))


def _parse_symbol_list(raw: str) -> list[str]:
    items = str(raw or "").replace("\n", ",").split(",")
    out: list[str] = []
    for item in items:
        sym = item.strip()
        if sym:
            out.append(sym)
    return out


def _guided_ui_state() -> dict:
    ui = st.session_state.get("mf6_guided_ui")
    if not isinstance(ui, dict):
        ui = {"action": "refresh", "preset": "safe_paper"}
        st.session_state["mf6_guided_ui"] = ui
    if not (isinstance(ui.get("summary"), dict) and isinstance(ui.get("preflight"), dict) and isinstance(ui.get("status"), dict)):
        ui["action"] = "refresh"
        render_guided_setup_panel(ui)
    return ui


def _guided_apply(action: str, *, preset: str | None = None, patch: dict | None = None) -> None:
    ui = _guided_ui_state()
    ui["action"] = action
    if preset is not None:
        ui["preset"] = str(preset)
    if patch is not None:
        ui["patch"] = patch
    render_guided_setup_panel(ui)
    st.session_state["mf6_guided_ui"] = ui


def _render_guided_setup() -> None:
    st.subheader("Guided Setup")
    st.caption("Review readiness, apply safe presets, and patch core runtime settings.")

    ui = _guided_ui_state()
    summary = ui.get("summary") or {}
    preflight = ui.get("preflight") or {}
    status = ui.get("status") or {}

    symbols = list(summary.get("symbols") or [])
    symbol_count = int(summary.get("symbol_count") or len(symbols))
    preflight_ok = bool(preflight.get("ok", preflight.get("ready", False)))

    m0, m1, m2, m3 = st.columns(4)
    m0.metric("Exchange", str(summary.get("exchange") or "-"))
    m1.metric("Symbols", str(symbol_count))
    m2.metric("Mode", str(summary.get("executor_mode") or "paper"))
    m3.metric("Preflight", "OK" if preflight_ok else "BLOCKED")

    cache = status.get("cache") if isinstance(status.get("cache"), dict) else {}
    kill_switch = status.get("kill_switch") if isinstance(status.get("kill_switch"), dict) else {}
    missing_pairs_count = int(cache.get("missing_pairs_count") or 0)

    if not preflight_ok:
        problems = preflight.get("problems") if isinstance(preflight.get("problems"), list) else []
        msg = ", ".join(str(x) for x in problems if str(x).strip()) or "preflight reported blocking checks"
        st.warning(f"Preflight is not ready: {msg}")
    if missing_pairs_count > 0:
        st.warning(f"Market cache is missing {missing_pairs_count} required pair(s). Populate cache before arming live mode.")
    if bool(kill_switch.get("armed")):
        st.info("Kill switch is armed (safe default).")

    c0, c1, c2 = st.columns([2, 1, 1])
    preset = c0.selectbox(
        "Risk preset",
        GUIDED_SETUP_PRESETS,
        index=0,
        format_func=_guided_preset_label,
        key="mf6_guided_preset",
    )
    if c1.button("Apply preset", use_container_width=True, key="mf6_guided_apply_preset"):
        _guided_apply("apply_preset", preset=preset)
        st.rerun()
    if c2.button("Refresh", use_container_width=True, key="mf6_guided_refresh"):
        _guided_apply("refresh")
        st.rerun()

    default_exchange = str(summary.get("exchange") or "coinbase")
    default_symbols = ", ".join(symbols or ["BTC/USD"])
    default_strategy = str(summary.get("strategy") or "ema")
    default_timeframe = str(summary.get("timeframe") or "5m")
    current_mode = str(summary.get("executor_mode") or "paper").lower().strip()
    mode_index = 1 if current_mode == "live" else 0

    with st.expander("Custom Patch", expanded=False):
        exchange_value = st.text_input("Exchange", value=default_exchange, key="mf6_patch_exchange")
        symbol_text = st.text_input("Symbols (comma separated)", value=default_symbols, key="mf6_patch_symbols")
        strategy_value = st.text_input("Strategy", value=default_strategy, key="mf6_patch_strategy")
        timeframe_value = st.text_input("Timeframe", value=default_timeframe, key="mf6_patch_timeframe")
        mode_value = st.selectbox("Executor mode", ["paper", "live"], index=mode_index, key="mf6_patch_mode")
        live_enabled_value = st.checkbox(
            "Enable live execution (explicit)",
            value=bool(summary.get("live_enabled", False)),
            key="mf6_patch_live_enabled",
        )

        patch = {
            "symbols": _parse_symbol_list(symbol_text) or ["BTC/USD"],
            "pipeline": {
                "exchange_id": str(exchange_value or "coinbase").strip().lower(),
                "strategy": str(strategy_value or "ema").strip(),
                "timeframe": str(timeframe_value or "5m").strip(),
            },
            "execution": {
                "executor_mode": mode_value,
                "live_enabled": bool(live_enabled_value),
            },
        }
        st.code(json.dumps(patch, indent=2), language="json")
        if st.button("Apply patch", use_container_width=True, key="mf6_guided_apply_patch"):
            _guided_apply("apply_patch", patch=patch)
            st.rerun()

    with st.expander("Guided Setup JSON", expanded=False):
        st.json({"summary": summary, "preflight": preflight, "status": status})


def _synthetic_ohlcv(count: int, *, start_px: float = 100.0) -> list[list[float]]:
    rows: list[list[float]] = []
    n = max(30, int(count))
    seg = max(10, n // 3)
    prev_close = float(start_px)
    base_ts = 1_700_000_000_000

    for i in range(n):
        if i < seg:
            close_px = start_px - 0.32 * i
        elif i < 2 * seg:
            close_px = start_px - 0.32 * seg + 0.42 * (i - seg)
        else:
            close_px = start_px - 0.32 * seg + 0.42 * seg - 0.36 * (i - 2 * seg)

        # Periodic deterministic spikes force breakout-style edges in synthetic data.
        if i % 17 == 0:
            close_px += 0.8
        elif i % 19 == 0:
            close_px -= 0.8

        open_px = prev_close
        high_px = max(open_px, close_px) + 0.25
        low_px = min(open_px, close_px) - 0.25
        rows.append([float(base_ts + (i * 60_000)), float(open_px), float(high_px), float(low_px), float(close_px), 1.0])
        prev_close = close_px
    return rows


def _op(args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "op.py")] + args
    p = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()

st.title("Operator")
st.caption("Start/stop services, view status, tail logs. Live remains locked by WizardState.")
AUTH_STATE = require_authenticated_role("OPERATOR")
_render_guided_setup()
st.divider()

rc_list, out_list = _op(["list"])
services = [x.strip() for x in out_list.splitlines() if x.strip()]
if not services:
    services = ["tick_publisher", "intent_reconciler", "intent_executor"]

c0, c1, c2, c3 = st.columns(4)
if c0.button("Preflight", use_container_width=True, key="op_preflight"):
    rc, out = _op(["preflight"])
    st.code(out or f"rc={rc}")

if c1.button("Start All", use_container_width=True, key="op_start_all"):
    rc, out = _op(["start-all"])
    st.code(out or f"rc={rc}")

if c2.button("Stop All", use_container_width=True, key="op_stop_all"):
    rc, out = _op(["stop-all"])
    st.code(out or f"rc={rc}")

if c3.button("Restart All", use_container_width=True, key="op_restart_all"):
    rc, out = _op(["restart-all"])
    st.code(out or f"rc={rc}")

if st.button("Stop Everything", use_container_width=True, key="op_stop_everything"):
    rc, out = _op(["stop-everything"])
    st.code(out or f"rc={rc}")

s0, s1, s2 = st.columns(3)
if s0.button("Supervisor Start", use_container_width=True, key="op_supervisor_start"):
    rc, out = _op(["supervisor-start"])
    st.code(out or f"rc={rc}")

if s1.button("Supervisor Stop", use_container_width=True, key="op_supervisor_stop"):
    rc, out = _op(["supervisor-stop"])
    st.code(out or f"rc={rc}")

if s2.button("Supervisor Status", use_container_width=True, key="op_supervisor_status"):
    rc, out = _op(["supervisor-status"])
    st.code(out or f"rc={rc}")

st.divider()

svc = st.selectbox("Service", services, index=0, key="op_service_select_unique")

d0, d1, d2, d3 = st.columns(4)
if d0.button("Status", use_container_width=True, key="op_status_one"):
    rc, out = _op(["status", "--name", svc])
    st.code(out or f"rc={rc}")

if d1.button("Start", use_container_width=True, key="op_start_one"):
    rc, out = _op(["start", "--name", svc])
    st.code(out or f"rc={rc}")

if d2.button("Stop", use_container_width=True, key="op_stop_one"):
    rc, out = _op(["stop", "--name", svc])
    st.code(out or f"rc={rc}")

if d3.button("Restart", use_container_width=True, key="op_restart_one"):
    rc, out = _op(["restart", "--name", svc])
    st.code(out or f"rc={rc}")

st.divider()

e0, e1 = st.columns(2)
if e0.button("Status All", use_container_width=True, key="op_status_all"):
    rc, out = _op(["status-all"])
    st.code(out or f"rc={rc}")

if e1.button("Diag", use_container_width=True, key="op_diag"):
    rc, out = _op(["diag", "--lines", "60"])
    st.code(out or f"rc={rc}")

st.divider()

n = st.number_input("Log tail lines", min_value=10, max_value=500, value=80, step=10, key="op_log_lines")
if st.button("Tail Logs", key="op_tail_logs"):
    rc, out = _op(["logs", "--name", svc, "--lines", str(int(n))])
    st.code(out or f"(no logs) rc={rc}")

if st.button("Clean Locks", key="op_clean_locks"):
    rc, out = _op(["clean"])
    st.code(out or f"rc={rc}")

st.divider()

if st.button("Show Live Gate Inputs", key="op_live_gate_inputs"):
    gate_cmd = [sys.executable, str(REPO_ROOT / "scripts" / "show_live_gate_inputs.py")]
    gate_proc = subprocess.run(gate_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    gate_out = (gate_proc.stdout or "") + (gate_proc.stderr or "")
    if gate_proc.returncode != 0:
        st.error(f"command failed (rc={gate_proc.returncode})\n{gate_out}")
    else:
        try:
            payload = json.loads(gate_out)
            st.json(payload)
        except Exception:
            st.code(gate_out or "(no output)")

if st.button("Run Reconcile Safe Steps", key="op_reconcile_safe_steps"):
    safe_cmd = [sys.executable, str(REPO_ROOT / "scripts" / "run_reconcile_safe_steps.py"), "--venue", "coinbase", "--symbols", "BTC/USD"]
    safe_proc = subprocess.run(safe_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    safe_out = (safe_proc.stdout or "") + (safe_proc.stderr or "")
    if safe_proc.returncode != 0:
        st.warning(f"safe-steps completed with warnings/errors (rc={safe_proc.returncode})")
    try:
        st.json(json.loads(safe_out))
    except Exception:
        st.code(safe_out or "(no output)")

st.divider()
st.subheader("Order Blocked Inspector")
st.caption("Inspect recent idempotency failures and copy an idempotency key for investigation.")

fi3_last10 = st.checkbox("Show last 10 failures only", value=True, key="fi3_last10")
fi3_venue = st.text_input("Venue filter (optional)", value="", key="fi3_venue_filter")
fi3_symbol = st.text_input("Symbol filter (optional)", value="", key="fi3_symbol_filter")

limit = 10 if fi3_last10 else 50
if st.button("Refresh failures", key="fi3_refresh"):
    st.session_state["fi3_snapshot"] = list_idem_recent(limit=limit, status="error")

snap = st.session_state.get("fi3_snapshot")
if not isinstance(snap, dict):
    snap = list_idem_recent(limit=limit, status="error")

if not bool(snap.get("ok")):
    reason = snap.get("reason") or "unknown_error"
    st.info(f"No failure data available yet ({reason}).")
else:
    rows = filter_idem_rows(list(snap.get("rows") or []), fi3_venue, fi3_symbol)
    st.caption(
        f"Source: {snap.get('path')}  Table: {snap.get('table')}  "
        f"Rows shown: {len(rows)} (limit={limit})"
    )
    if not rows:
        st.info("No failures match current filters.")
    else:
        copied = st.session_state.get("fi3_copied_key")
        if copied:
            st.text_input("Copied key", value=str(copied), key="fi3_copied_key_view")

        for idx, row in enumerate(rows):
            key = str(row.get("key") or "")
            title = (
                f"#{idx + 1} status={row.get('status') or '-'} "
                f"venue={row.get('venue') or '-'} symbol={row.get('symbol') or '-'}"
            )
            with st.expander(title):
                c_key, c_btn = st.columns([4, 1])
                c_key.code(key or "(empty key)")
                if c_btn.button("Copy key", key=f"fi3_copy_{idx}"):
                    st.session_state["fi3_copied_key"] = key
                    st.rerun()
                st.json(
                    {
                        "key": key,
                        "status": row.get("status"),
                        "ts": row.get("ts"),
                        "venue": row.get("venue"),
                        "symbol": row.get("symbol"),
                        "payload": row.get("payload"),
                        "raw": row.get("raw"),
                    }
                )

st.divider()
st.subheader("Strategy Params & Presets")
st.caption("Validate strategy parameters and safely write strategy/preset changes into runtime user config.")

cfg_user = load_user_yaml()
cur_st = cfg_user.get("strategy") if isinstance(cfg_user.get("strategy"), dict) else {}
strategy_names = supported_strategies()
cur_name = str(cur_st.get("name") or "ema_cross")
if cur_name not in strategy_names:
    cur_name = "ema_cross"
name_idx = strategy_names.index(cur_name)

selected_strategy = st.selectbox("Strategy", strategy_names, index=name_idx, key="hr7_strategy_name")
trade_enabled = st.checkbox(
    "Trade enabled",
    value=bool(cur_st.get("trade_enabled", True)),
    key="hr7_trade_enabled",
)

param_values: dict[str, float | int] = {}
if selected_strategy == "ema_cross":
    param_values["ema_fast"] = int(st.number_input("ema_fast", min_value=1, max_value=500, value=int(cur_st.get("ema_fast", 12)), key="hr7_ema_fast"))
    param_values["ema_slow"] = int(st.number_input("ema_slow", min_value=2, max_value=1000, value=int(cur_st.get("ema_slow", 26)), key="hr7_ema_slow"))
elif selected_strategy == "mean_reversion_rsi":
    param_values["rsi_len"] = int(st.number_input("rsi_len", min_value=2, max_value=200, value=int(cur_st.get("rsi_len", 14)), key="hr7_rsi_len"))
    param_values["sma_len"] = int(st.number_input("sma_len", min_value=2, max_value=500, value=int(cur_st.get("sma_len", 50)), key="hr7_sma_len"))
    param_values["rsi_buy"] = float(st.number_input("rsi_buy", min_value=0.0, max_value=100.0, value=float(cur_st.get("rsi_buy", 30.0)), key="hr7_rsi_buy"))
    param_values["rsi_sell"] = float(st.number_input("rsi_sell", min_value=0.0, max_value=100.0, value=float(cur_st.get("rsi_sell", 70.0)), key="hr7_rsi_sell"))
else:
    param_values["donchian_len"] = int(st.number_input("donchian_len", min_value=2, max_value=500, value=int(cur_st.get("donchian_len", 20)), key="hr7_donchian_len"))

try:
    preview_block = build_strategy_block(
        name=selected_strategy,
        trade_enabled=trade_enabled,
        params=param_values,
    )
    preview_cfg = apply_strategy_block(cfg_user, preview_block)
    preview_validation = validate_cfg(preview_cfg)
except Exception as e:
    preview_cfg = cfg_user
    preview_validation = {"ok": False, "errors": [f"{type(e).__name__}:{e}"], "warnings": [], "strategy": selected_strategy}

v0, v1 = st.columns(2)
if v0.button("Validate Strategy Params", key="hr7_validate"):
    if bool(preview_validation.get("ok")):
        st.success("Strategy parameters look valid.")
    else:
        st.error("Strategy parameters are invalid.")
    errs = list(preview_validation.get("errors") or [])
    warns = list(preview_validation.get("warnings") or [])
    if errs:
        st.code("\n".join(str(x) for x in errs))
    if warns:
        st.warning("\n".join(str(x) for x in warns))

if v1.button("Save Strategy Params", key="hr7_save"):
    if not bool(preview_validation.get("ok")):
        st.error("Refusing to save invalid strategy config.")
    else:
        ok, msg = save_user_yaml(preview_cfg)
        if ok:
            st.success(f"Saved strategy settings: {msg}")
        else:
            st.error(f"Save failed: {msg}")

preset_names = list_presets()
if preset_names:
    preset_name = st.selectbox("Preset", preset_names, index=0, key="jp8_preset_name")
    if st.button("Apply Preset (Save)", key="jp8_apply_preset"):
        try:
            next_cfg, vr = apply_preset_and_validate(cfg_user, preset_name)
            if not bool(vr.get("ok")):
                st.error("Preset produced invalid strategy config; not saved.")
                st.code("\n".join(str(x) for x in list(vr.get("errors") or [])))
            else:
                ok, msg = save_user_yaml(next_cfg)
                if ok:
                    st.success(f"Applied preset and saved: {preset_name}")
                else:
                    st.error(f"Save failed: {msg}")
        except Exception as e:
            st.error(f"Apply preset failed: {type(e).__name__}: {e}")

st.divider()
st.subheader("Backtest Parity")
st.caption("Run deterministic parity backtests for the selected strategy on synthetic OHLCV and inspect trades/metrics.")

ih6_symbol = st.text_input("Backtest symbol", value="BTC/USD", key="ih6_symbol")
ih6_bars = int(st.slider("Synthetic bars", min_value=60, max_value=720, value=180, step=30, key="ih6_bars"))
ih6_warmup = int(st.slider("Warmup bars", min_value=1, max_value=120, value=50, step=1, key="ih6_warmup"))
ih6_initial_cash = float(st.number_input("Initial cash", min_value=100.0, max_value=1_000_000.0, value=10_000.0, step=100.0, key="ih6_initial_cash"))
ih6_fee_bps = float(st.number_input("Fee (bps)", min_value=0.0, max_value=100.0, value=10.0, step=0.5, key="ih6_fee_bps"))
ih6_slippage_bps = float(st.number_input("Slippage (bps)", min_value=0.0, max_value=100.0, value=5.0, step=0.5, key="ih6_slippage_bps"))

if st.button("Run Backtest Parity", key="ih6_run"):
    ih6_candles = _synthetic_ohlcv(ih6_bars)
    try:
        ih6_cfg = apply_strategy_block(cfg_user, preview_block)
        st.session_state["ih6_result"] = run_parity_backtest(
            cfg=ih6_cfg,
            symbol=str(ih6_symbol or "BTC/USD"),
            candles=ih6_candles,
            warmup_bars=int(ih6_warmup),
            initial_cash=float(ih6_initial_cash),
            fee_bps=float(ih6_fee_bps),
            slippage_bps=float(ih6_slippage_bps),
        )
    except Exception as e:
        st.session_state["ih6_result"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}

ih6_result = st.session_state.get("ih6_result")
if isinstance(ih6_result, dict):
    if not bool(ih6_result.get("ok")):
        st.error(str(ih6_result.get("error") or "backtest_failed"))
    else:
        m = ih6_result.get("metrics") if isinstance(ih6_result.get("metrics"), dict) else {}
        m0, m1, m2, m3 = st.columns(4)
        m0.metric("Trades", str(int(ih6_result.get("trade_count") or 0)))
        m1.metric("Final Equity", f"{float(m.get('final_equity', 0.0)):.2f}")
        m2.metric("Return %", f"{float(m.get('total_return_pct', 0.0)):.2f}")
        m3.metric("Max DD %", f"{float(m.get('max_drawdown_pct', 0.0)):.2f}")
        trades = list(ih6_result.get("trades") or [])
        if trades:
            st.caption("Recent trades")
            st.dataframe(trades[-20:], use_container_width=True, hide_index=True)
        eq = list(ih6_result.get("equity") or [])
        if eq:
            st.caption("Equity curve")
            st.line_chart([float(x.get("equity") or 0.0) for x in eq], use_container_width=True)

st.divider()
st.subheader("Repair/Reset Wizard")
st.caption("Run preflight self-checks, preview reset impact, and execute reset only after typed confirmation.")

rw_include_locks = st.checkbox("Include lock files in reset", value=False, key="rw_include_locks")
rw_confirm = st.text_input(
    f"Type `{REPAIR_CONFIRM_TEXT}` to allow execute",
    value="",
    key="rw_confirm_text",
)
r0, r1, r2 = st.columns(3)
if r0.button("Run Self-Check", key="rw_self_check"):
    st.json(preflight_self_check())
if r1.button("Preview Reset", key="rw_preview_reset"):
    st.json(preview_reset(include_locks=rw_include_locks))
if r2.button("Execute Reset", key="rw_execute_reset"):
    st.json(execute_reset(confirm_text=rw_confirm, include_locks=rw_include_locks))
