from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.rotation_engine import build_rotation_candidates
from services.risk.allocation_engine import build_allocation_limits, allocate_budget
from services.risk.execution_planner import build_execution_plan, summarize_current_allocations
from storage.paper_trading_sqlite import PaperTradingSQLite

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Execution Plan")
st.caption("Build a rebalance plan from diversified rotation candidates and target allocation.")

col0, col1, col2, col3, col4 = st.columns([1, 1, 1, 1, 1])
with col0:
    top_n = st.slider("Top candidates", min_value=3, max_value=15, value=8, step=1)
with col1:
    total_budget = st.slider("Target deployment %", min_value=10.0, max_value=100.0, value=60.0, step=5.0)
with col2:
    portfolio_value = st.number_input("Portfolio value", min_value=100.0, value=10000.0, step=500.0)
with col3:
    min_delta_pct = st.slider("Min rebalance delta %", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
with col4:
    run_now = st.button("Build Execution Plan", width="stretch")

if "execution_plan_result" not in st.session_state:
    st.session_state["execution_plan_result"] = None
if "execution_queue_result" not in st.session_state:
    st.session_state["execution_queue_result"] = None

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

        pdb = PaperTradingSQLite()
        positions = []
        try:
            if hasattr(pdb, "list_positions"):
                positions = list(pdb.list_positions() or [])
            elif hasattr(pdb, "get_all_positions"):
                positions = list(pdb.get_all_positions() or [])
            elif hasattr(pdb, "positions"):
                positions = list(pdb.positions() or [])
        except Exception:
            positions = []

        current_allocations = summarize_current_allocations(
            positions=positions,
        )

        plan_symbols = [str(r.get("symbol") or "").strip() for r in (allocation.get("rows") or []) if str(r.get("symbol") or "").strip()]
        price_map = resolve_prices(symbols=plan_symbols, venue="coinbase")

        plan = build_execution_plan(
            target_rows=list(allocation.get("rows") or []),
            current_allocations=current_allocations,
            min_rebalance_delta_pct=min_delta_pct,
            price_map=price_map,
            portfolio_value=float(portfolio_value),
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

queue_now = st.button("Queue Execution Intents", width="stretch")
if queue_now:
    st.session_state["execution_queue_result"] = queue_execution_intents(
        plan_rows=list(plan.get("rows") or []),
        strategy_name="allocation_rebalance",
        venue="coinbase",
        min_delta_pct=min_delta_pct,
    )

current_allocations = {}
for row in plan.get("rows") or []:
    sym = str(row.get("symbol") or "").strip()
    cur = float(row.get("current_alloc_pct") or 0.0)
    if sym and cur > 0:
        current_allocations[sym] = cur

st.subheader("Current Allocations")
st.write(current_allocations)

st.subheader("Execution Plan")
st.dataframe(plan.get("rows", []), use_container_width=True)

st.subheader("Buy List")
st.dataframe(plan.get("buys", []), use_container_width=True)

st.subheader("Sell List")
st.dataframe(plan.get("sells", []), use_container_width=True)

queue_result = st.session_state.get("execution_queue_result")
if queue_result is not None:
    q0, q1, q2 = st.columns(3)
    q0.metric("Queued", len(queue_result.get("queued") or []))
    q1.metric("Skipped", len(queue_result.get("skipped") or []))
    q2.metric("Errors", len(queue_result.get("errors") or []))

    st.subheader("Queued Intents")
    st.dataframe(queue_result.get("queued", []), use_container_width=True)

    st.subheader("Skipped Intents")
    st.dataframe(queue_result.get("skipped", []), use_container_width=True)

    st.subheader("Queue Errors")
    st.dataframe(queue_result.get("errors", []), use_container_width=True)
