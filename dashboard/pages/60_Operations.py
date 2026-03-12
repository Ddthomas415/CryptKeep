from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.actions import render_system_action_buttons
from dashboard.components.header import render_page_header
from dashboard.components.logs import render_action_result
from dashboard.services.operator import list_services, run_op
from dashboard.state.session import get_operator_result, set_operator_result


AUTH_STATE = require_authenticated_role("OPERATOR")

render_page_header(
    "Operations",
    "Advanced system controls and logs are isolated from user-facing workflow pages.",
    badges=[
        {"label": "User", "value": str(AUTH_STATE.get("username") or "unknown")},
        {"label": "Role", "value": str(AUTH_STATE.get("role") or "OPERATOR")},
    ],
)

tab_tools, tab_service_logs = st.tabs(["System Tools", "Service Logs"])

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

st.warning("Legacy Operator page remains available for full compatibility and deep tooling.")
