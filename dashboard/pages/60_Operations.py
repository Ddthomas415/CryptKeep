from __future__ import annotations

import json

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.actions import render_system_action_buttons
from dashboard.components.header import render_page_header
from dashboard.components.logs import render_action_result
from dashboard.services.operator import list_services, run_op, run_repo_script
from dashboard.state.session import get_operator_result, set_operator_result
from services.admin.repair_wizard import CONFIRM_TEXT as REPAIR_CONFIRM_TEXT
from services.admin.repair_wizard import execute_reset, preflight_self_check, preview_reset
from services.execution.idempotency_inspector import filter_rows as filter_idem_rows
from services.execution.idempotency_inspector import list_recent as list_idem_recent


AUTH_STATE = require_authenticated_role("OPERATOR")

render_page_header(
    "Operations",
    "Advanced system controls and logs are isolated from user-facing workflow pages.",
    badges=[
        {"label": "User", "value": str(AUTH_STATE.get("username") or "unknown")},
        {"label": "Role", "value": str(AUTH_STATE.get("role") or "OPERATOR")},
    ],
)

tab_tools, tab_service_logs, tab_failures, tab_safety = st.tabs(
    ["System Tools", "Service Logs", "Order Blocked Inspector", "Safety & Recovery"]
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

st.warning("Legacy Operator page remains available for full compatibility and deep tooling.")
