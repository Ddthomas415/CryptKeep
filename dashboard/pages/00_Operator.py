from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

_st_button = st.button


def _disabled_button(label: str, *args, **kwargs):
    if isinstance(label, str) and "Start Live Bot" in label:
        kwargs["disabled"] = True
        return False
    return _st_button(label, *args, **kwargs)


st.button = _disabled_button

REPO_ROOT = Path(__file__).resolve().parents[2]

def _op(args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "op.py")] + args
    p = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()

st.title("Operator")
st.caption("Start/stop services, view status, tail logs. Live remains locked by WizardState.")

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
