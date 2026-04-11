from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.execution.paper_reconciliation import reconcile_execution_plan_intents

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Paper Reconciliation")
st.caption("Apply queued execution-plan intents into paper positions and mark intents filled. Uses live market prices when available, otherwise falls back to the default fill price. Reconciliation now prefers queued size metadata, then notional metadata, then allocation fallback.")

col0, col1, col2 = st.columns([1, 1, 1])
with col0:
    venue = st.selectbox("Venue", ["coinbase", "kraken"], index=0)
with col1:
    default_fill_price = st.number_input("Default fill price", min_value=0.01, value=100.0, step=1.0)
with col2:
    run_now = st.button("Run Reconciliation", width="stretch")

if "paper_recon_result" not in st.session_state:
    st.session_state["paper_recon_result"] = None

if run_now:
    with st.spinner("Reconciling queued intents..."):
        st.session_state["paper_recon_result"] = reconcile_execution_plan_intents(
            default_fill_price=float(default_fill_price),
            venue=str(venue),
        )

result = st.session_state.get("paper_recon_result")

if result is None:
    st.info("Click 'Run Reconciliation' to fill queued execution-plan intents into paper state.")
    st.stop()

c0, c1, c2 = st.columns(3)
c0.metric("Filled", len(result.get("filled", [])))
c1.metric("Skipped", len(result.get("skipped", [])))
c2.metric("Errors", len(result.get("errors", [])))

st.subheader("Filled")
st.dataframe(result.get("filled", []), use_container_width=True)

st.subheader("Skipped")
st.dataframe(result.get("skipped", []), use_container_width=True)

st.subheader("Errors")
st.dataframe(result.get("errors", []), use_container_width=True)
