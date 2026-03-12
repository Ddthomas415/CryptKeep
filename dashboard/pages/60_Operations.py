from __future__ import annotations

import json

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.actions import render_system_action_buttons
from dashboard.components.header import render_page_header
from dashboard.components.logs import render_action_result
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_operations_status_summary
from dashboard.services.operator import get_operations_snapshot, list_services, run_op, run_repo_script
from dashboard.services.operator_tools import synthetic_ohlcv
from dashboard.state.session import get_operator_result, set_operator_result
from services.admin.repair_wizard import CONFIRM_TEXT as REPAIR_CONFIRM_TEXT
from services.admin.repair_wizard import execute_reset, preflight_self_check, preview_reset
from services.admin.config_editor import load_user_yaml, save_user_yaml
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


AUTH_STATE = require_authenticated_role("OPERATOR")
render_app_sidebar()

render_page_header(
    "Operations",
    "Advanced system controls and logs are isolated from user-facing workflow pages.",
    badges=[
        {"label": "User", "value": str(AUTH_STATE.get("username") or "unknown")},
        {"label": "Role", "value": str(AUTH_STATE.get("role") or "OPERATOR")},
    ],
)

render_operations_status_summary(get_operations_snapshot())

tab_tools, tab_service_logs, tab_failures, tab_strategy, tab_safety = st.tabs(
    ["System Tools", "Service Logs", "Order Blocked Inspector", "Strategy & Backtest", "Safety & Recovery"]
)

with tab_tools:
    action = render_system_action_buttons()
    if action:
        label, args = action
        rc, out = run_op(args)
        set_operator_result(action=label, rc=rc, output=out or "(no output)")

    result = get_operator_result()
    render_action_result(
        action=str(result.get("action") or ""),
        rc=int(result["rc"]) if result.get("rc") is not None else None,
        output=str(result.get("output") or ""),
    )

with tab_service_logs:
    services = list_services()

    service_name = st.selectbox("Service", services, index=0)
    lines = st.number_input("Lines", min_value=20, max_value=500, value=120, step=10)
    b0, b1, b2, b3 = st.columns(4)
    if b0.button("Status", use_container_width=True, key="ops_service_status"):
        rc, out = run_op(["status", "--name", str(service_name)])
        set_operator_result(action="Status", rc=rc, output=out or "(no output)")
    if b1.button("Start", use_container_width=True, key="ops_service_start"):
        rc, out = run_op(["start", "--name", str(service_name)])
        set_operator_result(action="Start", rc=rc, output=out or "(no output)")
    if b2.button("Stop", use_container_width=True, key="ops_service_stop"):
        rc, out = run_op(["stop", "--name", str(service_name)])
        set_operator_result(action="Stop", rc=rc, output=out or "(no output)")
    if b3.button("Restart", use_container_width=True, key="ops_service_restart"):
        rc, out = run_op(["restart", "--name", str(service_name)])
        set_operator_result(action="Restart", rc=rc, output=out or "(no output)")

    if st.button("Tail Logs", use_container_width=True, key="ops_tail_logs"):
        rc, out = run_op(["logs", "--name", str(service_name), "--lines", str(int(lines))])
        set_operator_result(action="Tail Logs", rc=rc, output=out or "(no output)")

    result = get_operator_result()
    render_action_result(
        action=str(result.get("action") or ""),
        rc=int(result["rc"]) if result.get("rc") is not None else None,
        output=str(result.get("output") or ""),
    )

with tab_failures:
    st.caption("Inspect recent idempotency failures and copy an idempotency key for investigation.")
    show_last_10 = st.checkbox("Show last 10 failures only", value=True, key="ops_fi3_last10")
    venue_filter = st.text_input("Venue filter (optional)", value="", key="ops_fi3_venue_filter")
    symbol_filter = st.text_input("Symbol filter (optional)", value="", key="ops_fi3_symbol_filter")

    limit = 10 if show_last_10 else 50
    if st.button("Refresh failures", key="ops_fi3_refresh"):
        st.session_state["ops_fi3_snapshot"] = list_idem_recent(limit=limit, status="error")

    snapshot = st.session_state.get("ops_fi3_snapshot")
    if not isinstance(snapshot, dict):
        snapshot = list_idem_recent(limit=limit, status="error")

    if not bool(snapshot.get("ok")):
        reason = snapshot.get("reason") or "unknown_error"
        st.info(f"No failure data available yet ({reason}).")
    else:
        rows = filter_idem_rows(list(snapshot.get("rows") or []), venue_filter, symbol_filter)
        st.caption(
            f"Source: {snapshot.get('path')}  Table: {snapshot.get('table')}  "
            f"Rows shown: {len(rows)} (limit={limit})"
        )
        if not rows:
            st.info("No failures match current filters.")
        else:
            copied = st.session_state.get("ops_fi3_copied_key")
            if copied:
                st.text_input("Copied key", value=str(copied), key="ops_fi3_copied_key_view")

            for idx, row in enumerate(rows):
                key = str(row.get("key") or "")
                title = (
                    f"#{idx + 1} status={row.get('status') or '-'} "
                    f"venue={row.get('venue') or '-'} symbol={row.get('symbol') or '-'}"
                )
                with st.expander(title):
                    c_key, c_btn = st.columns([4, 1])
                    c_key.code(key or "(empty key)")
                    if c_btn.button("Copy key", key=f"ops_fi3_copy_{idx}"):
                        st.session_state["ops_fi3_copied_key"] = key
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

with tab_strategy:
    st.caption("Validate and save strategy parameters, then run parity backtests on synthetic candles.")

    cfg_user = load_user_yaml()
    cur_st = cfg_user.get("strategy") if isinstance(cfg_user.get("strategy"), dict) else {}
    strategy_names = supported_strategies()
    cur_name = str(cur_st.get("name") or "ema_cross")
    if cur_name not in strategy_names:
        cur_name = "ema_cross"
    name_idx = strategy_names.index(cur_name)

    selected_strategy = st.selectbox(
        "Strategy",
        strategy_names,
        index=name_idx,
        key="ops_hr7_strategy_name",
    )
    trade_enabled = st.checkbox(
        "Trade enabled",
        value=bool(cur_st.get("trade_enabled", True)),
        key="ops_hr7_trade_enabled",
    )

    param_values: dict[str, float | int] = {}
    if selected_strategy == "ema_cross":
        param_values["ema_fast"] = int(
            st.number_input(
                "ema_fast",
                min_value=1,
                max_value=500,
                value=int(cur_st.get("ema_fast", 12)),
                key="ops_hr7_ema_fast",
            )
        )
        param_values["ema_slow"] = int(
            st.number_input(
                "ema_slow",
                min_value=2,
                max_value=1000,
                value=int(cur_st.get("ema_slow", 26)),
                key="ops_hr7_ema_slow",
            )
        )
    elif selected_strategy == "mean_reversion_rsi":
        param_values["rsi_len"] = int(
            st.number_input(
                "rsi_len",
                min_value=2,
                max_value=200,
                value=int(cur_st.get("rsi_len", 14)),
                key="ops_hr7_rsi_len",
            )
        )
        param_values["sma_len"] = int(
            st.number_input(
                "sma_len",
                min_value=2,
                max_value=500,
                value=int(cur_st.get("sma_len", 50)),
                key="ops_hr7_sma_len",
            )
        )
        param_values["rsi_buy"] = float(
            st.number_input(
                "rsi_buy",
                min_value=0.0,
                max_value=100.0,
                value=float(cur_st.get("rsi_buy", 30.0)),
                key="ops_hr7_rsi_buy",
            )
        )
        param_values["rsi_sell"] = float(
            st.number_input(
                "rsi_sell",
                min_value=0.0,
                max_value=100.0,
                value=float(cur_st.get("rsi_sell", 70.0)),
                key="ops_hr7_rsi_sell",
            )
        )
    else:
        param_values["donchian_len"] = int(
            st.number_input(
                "donchian_len",
                min_value=2,
                max_value=500,
                value=int(cur_st.get("donchian_len", 20)),
                key="ops_hr7_donchian_len",
            )
        )

    try:
        preview_block = build_strategy_block(
            name=selected_strategy,
            trade_enabled=trade_enabled,
            params=param_values,
        )
        preview_cfg = apply_strategy_block(cfg_user, preview_block)
        preview_validation = validate_cfg(preview_cfg)
    except Exception as exc:
        preview_cfg = cfg_user
        preview_validation = {
            "ok": False,
            "errors": [f"{type(exc).__name__}:{exc}"],
            "warnings": [],
            "strategy": selected_strategy,
        }

    v0, v1 = st.columns(2)
    if v0.button("Validate Strategy Params", key="ops_hr7_validate", use_container_width=True):
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

    if v1.button("Save Strategy Params", key="ops_hr7_save", use_container_width=True):
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
        preset_name = st.selectbox(
            "Preset",
            preset_names,
            index=0,
            key="ops_jp8_preset_name",
        )
        if st.button("Apply Preset (Save)", key="ops_jp8_apply_preset", use_container_width=True):
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
            except Exception as exc:
                st.error(f"Apply preset failed: {type(exc).__name__}: {exc}")

    st.markdown("### Backtest Parity")
    bt_symbol = st.text_input("Backtest symbol", value="BTC/USD", key="ops_ih6_symbol")
    bt_bars = int(st.slider("Synthetic bars", min_value=60, max_value=720, value=180, step=30, key="ops_ih6_bars"))
    bt_warmup = int(st.slider("Warmup bars", min_value=1, max_value=120, value=50, step=1, key="ops_ih6_warmup"))
    bt_initial_cash = float(
        st.number_input(
            "Initial cash",
            min_value=100.0,
            max_value=1_000_000.0,
            value=10_000.0,
            step=100.0,
            key="ops_ih6_initial_cash",
        )
    )
    bt_fee_bps = float(
        st.number_input(
            "Fee (bps)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
            key="ops_ih6_fee_bps",
        )
    )
    bt_slippage_bps = float(
        st.number_input(
            "Slippage (bps)",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=0.5,
            key="ops_ih6_slippage_bps",
        )
    )

    if st.button("Run Backtest Parity", key="ops_ih6_run", use_container_width=True):
        candles = synthetic_ohlcv(bt_bars)
        try:
            bt_cfg = apply_strategy_block(cfg_user, preview_block)
            st.session_state["ops_ih6_result"] = run_parity_backtest(
                cfg=bt_cfg,
                symbol=str(bt_symbol or "BTC/USD"),
                candles=candles,
                warmup_bars=int(bt_warmup),
                initial_cash=float(bt_initial_cash),
                fee_bps=float(bt_fee_bps),
                slippage_bps=float(bt_slippage_bps),
            )
        except Exception as exc:
            st.session_state["ops_ih6_result"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    result = st.session_state.get("ops_ih6_result")
    if isinstance(result, dict):
        if not bool(result.get("ok")):
            st.error(str(result.get("error") or "backtest_failed"))
        else:
            metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
            m0, m1, m2, m3 = st.columns(4)
            m0.metric("Trades", str(int(result.get("trade_count") or 0)))
            m1.metric("Final Equity", f"{float(metrics.get('final_equity', 0.0)):.2f}")
            m2.metric("Return %", f"{float(metrics.get('total_return_pct', 0.0)):.2f}")
            m3.metric("Max DD %", f"{float(metrics.get('max_drawdown_pct', 0.0)):.2f}")
            trades = list(result.get("trades") or [])
            if trades:
                st.caption("Recent trades")
                st.dataframe(trades[-20:], use_container_width=True, hide_index=True)
            equity = list(result.get("equity") or [])
            if equity:
                st.caption("Equity curve")
                st.line_chart([float(x.get("equity") or 0.0) for x in equity], use_container_width=True)

with tab_safety:
    st.caption("Live safety snapshots and repair/reset tooling.")
    s0, s1 = st.columns(2)
    if s0.button("Show Live Gate Inputs", use_container_width=True, key="ops_live_gate_inputs"):
        rc, out = run_repo_script("scripts/show_live_gate_inputs.py")
        payload: object
        if rc == 0:
            try:
                payload = json.loads(out)
            except Exception:
                payload = {"ok": False, "reason": "invalid_json_output", "raw": out}
        else:
            payload = {"ok": False, "reason": "command_failed", "rc": rc, "raw": out}
        set_operator_result(action="Show Live Gate Inputs", rc=rc, output=json.dumps(payload, indent=2))

    if s1.button("Run Reconcile Safe Steps", use_container_width=True, key="ops_reconcile_safe_steps"):
        rc, out = run_repo_script(
            "scripts/run_reconcile_safe_steps.py",
            args=["--venue", "coinbase", "--symbols", "BTC/USD"],
        )
        payload: object
        try:
            payload = json.loads(out)
        except Exception:
            payload = {"ok": rc == 0, "rc": rc, "raw": out}
        set_operator_result(action="Run Reconcile Safe Steps", rc=rc, output=json.dumps(payload, indent=2))

    st.markdown("### Repair / Reset Wizard")
    include_locks = st.checkbox("Include lock files in reset", value=False, key="ops_rw_include_locks")
    confirm_text = st.text_input(
        f"Type `{REPAIR_CONFIRM_TEXT}` to allow execute",
        value="",
        key="ops_rw_confirm_text",
    )
    r0, r1, r2 = st.columns(3)
    if r0.button("Run Self-Check", use_container_width=True, key="ops_rw_self_check"):
        payload = preflight_self_check()
        set_operator_result(action="Run Self-Check", rc=0, output=json.dumps(payload, indent=2))
    if r1.button("Preview Reset", use_container_width=True, key="ops_rw_preview_reset"):
        payload = preview_reset(include_locks=include_locks)
        set_operator_result(action="Preview Reset", rc=0, output=json.dumps(payload, indent=2))
    if r2.button("Execute Reset", use_container_width=True, key="ops_rw_execute_reset"):
        payload = execute_reset(confirm_text=confirm_text, include_locks=include_locks)
        rc = 0 if bool(payload.get("ok")) else 1
        set_operator_result(action="Execute Reset", rc=rc, output=json.dumps(payload, indent=2))

    result = get_operator_result()
    render_action_result(
        action=str(result.get("action") or ""),
        rc=int(result["rc"]) if result.get("rc") is not None else None,
        output=str(result.get("output") or ""),
    )

st.info("Legacy Operator page now acts as a compatibility redirect to this Operations workspace.")
