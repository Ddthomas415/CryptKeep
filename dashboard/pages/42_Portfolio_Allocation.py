from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.rotation_engine import build_rotation_candidates
from services.risk.allocation_engine import build_allocation_limits, allocate_budget

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Portfolio Allocation")
st.caption("Ranked rotation candidates with target portfolio allocation percentages.")

col0, col1, col2 = st.columns([1, 1, 1])
with col0:
    top_n = st.slider("Top candidates", min_value=3, max_value=15, value=8, step=1)
with col1:
    total_budget = st.slider("Target deployment %", min_value=10.0, max_value=100.0, value=60.0, step=5.0)
with col2:
    run_now = st.button("Build Allocation", width="stretch")

if "allocation_result" not in st.session_state:
    st.session_state["allocation_result"] = None

if run_now:
    with st.spinner("Building allocation plan..."):
        rotation = build_rotation_candidates(top_n=top_n)
        limits = build_allocation_limits({"risk": {"target_total_deployment_pct": total_budget}})
        alloc = allocate_budget(
            ranked_rows=list(rotation.get("rows") or []),
            limits=limits,
            top_n=top_n,
        )
        st.session_state["allocation_result"] = {
            "rotation": rotation,
            "allocation": alloc,
        }

result = st.session_state.get("allocation_result")

if result is None:
    st.info("Click 'Build Allocation' to create the current target portfolio split.")
    st.stop()

rotation = result.get("rotation") or {}
allocation = result.get("allocation") or {}

c0, c1, c2 = st.columns(3)
c0.metric("Scanned", int(rotation.get("scanned", 0)))
c1.metric("Selected", len((allocation.get("rows") or [])))
c2.metric("Allocated %", float(allocation.get("total_allocated_pct", 0.0)))

st.subheader("Allocation Plan")
st.dataframe(allocation.get("rows", []), use_container_width=True)
