from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.rotation_engine import build_rotation_candidates
from services.risk.allocation_engine import build_allocation_limits, allocate_budget
from services.risk.execution_planner import build_execution_plan

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Execution Plan")
st.caption("Build a rebalance plan from diversified rotation candidates and target allocation.")

col0, col1, col2 = st.columns([1, 1, 1])
with col0:
    top_n = st.slider("Top candidates", min_value=3, max_value=15, value=8, step=1)
with col1:
    total_budget = st.slider("Target deployment %", min_value=10.0, max_value=100.0, value=60.0, step=5.0)
with col2:
    run_now = st.button("Build Execution Plan", width="stretch")

if "execution_plan_result" not in st.session_state:
    st.session_state["execution_plan_result"] = None

if run_now:
    with st.spinner("Building execution plan..."):
        rotation = build_rotation_candidates(top_n=top_n, diversify=True)
        limits = build_allocation_limits({"risk": {"target_total_deployment_pct": total_budget}})
        allocation = allocate_budget(
            ranked_rows=list(rotation.get("selected_rows") or rotation.get("rows") or []),
            limits=limits,
            top_n=top_n,
            correlation_matrix=((rotation.get("correlation") or {}).get("matrix") or {}),
        )

        # dashboard scaffold: assume no current positions yet
        current_allocations = {}

        plan = build_execution_plan(
            target_rows=list(allocation.get("rows") or []),
            current_allocations=current_allocations,
            min_rebalance_delta_pct=1.0,
        )

        st.session_state["execution_plan_result"] = {
            "rotation": rotation,
            "allocation": allocation,
            "plan": plan,
        }

result = st.session_state.get("execution_plan_result")

if result is None:
    st.info("Click 'Build Execution Plan' to generate the current rebalance plan.")
    st.stop()

allocation = result.get("allocation") or {}
plan = result.get("plan") or {}

c0, c1, c2, c3 = st.columns(4)
c0.metric("Targets", len(allocation.get("rows") or []))
c1.metric("Buys", len(plan.get("buys") or []))
c2.metric("Sells", len(plan.get("sells") or []))
c3.metric("Holds", len(plan.get("holds") or []))

st.subheader("Execution Plan")
st.dataframe(plan.get("rows", []), use_container_width=True)

st.subheader("Buy List")
st.dataframe(plan.get("buys", []), use_container_width=True)

st.subheader("Sell List")
st.dataframe(plan.get("sells", []), use_container_width=True)
