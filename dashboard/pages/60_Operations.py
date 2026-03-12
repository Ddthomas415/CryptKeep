from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header

REPO_ROOT = Path(__file__).resolve().parents[2]


def _op(args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "op.py")] + args
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return int(proc.returncode), output.strip()


def _run_and_store(label: str, args: list[str]) -> None:
    rc, out = _op(args)
    st.session_state["ops_last_action"] = label
    st.session_state["ops_last_rc"] = rc
    st.session_state["ops_last_output"] = out or "(no output)"


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
    c0, c1, c2, c3 = st.columns(4)
    if c0.button("Preflight", use_container_width=True):
        _run_and_store("Preflight", ["preflight"])
    if c1.button("Status All", use_container_width=True):
        _run_and_store("Status All", ["status-all"])
    if c2.button("Diagnostic", use_container_width=True):
        _run_and_store("Diagnostic", ["diag", "--lines", "80"])
    if c3.button("Clean Locks", use_container_width=True):
        _run_and_store("Clean Locks", ["clean"])

    c4, c5 = st.columns(2)
    if c4.button("Start All", use_container_width=True):
        _run_and_store("Start All", ["start-all"])
    if c5.button("Stop All", use_container_width=True):
        _run_and_store("Stop All", ["stop-all"])

    if st.session_state.get("ops_last_action"):
        st.markdown("### Action Result")
        st.caption(
            f"{st.session_state.get('ops_last_action')} (rc={st.session_state.get('ops_last_rc', '-')})"
        )
        st.code(str(st.session_state.get("ops_last_output") or "(no output)"))

with tab_service_logs:
    rc, out = _op(["list"])
    services = [line.strip() for line in out.splitlines() if line.strip()] if rc == 0 else []
    if not services:
        services = ["tick_publisher", "intent_reconciler", "intent_executor"]

    service_name = st.selectbox("Service", services, index=0)
    lines = st.number_input("Lines", min_value=20, max_value=500, value=120, step=10)

    if st.button("Tail Logs", use_container_width=True):
        _run_and_store("Tail Logs", ["logs", "--name", str(service_name), "--lines", str(int(lines))])

    if st.session_state.get("ops_last_action") == "Tail Logs":
        st.code(str(st.session_state.get("ops_last_output") or "(no output)"))

st.warning("Legacy Operator page remains available for full compatibility and deep tooling.")
