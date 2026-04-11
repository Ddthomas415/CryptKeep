from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.execution.outcome_summary import load_outcomes, summarize_outcomes

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Runtime Outcome Summary")
st.caption("Summary of realized paper outcomes by selected strategy and regime.")

limit = st.slider("Rows to load", min_value=50, max_value=5000, value=500, step=50)

rows = load_outcomes(limit=limit)
summary = summarize_outcomes(rows)

c0, c1 = st.columns(2)
c0.metric("Loaded outcomes", int(summary.get("count", 0)))
c1.metric("Strategies seen", len(summary.get("by_strategy") or []))

st.subheader("By Strategy")
st.dataframe(summary.get("by_strategy", []), use_container_width=True)

st.subheader("By Regime")
st.dataframe(summary.get("by_regime", []), use_container_width=True)

st.subheader("Strategy × Regime")
st.dataframe(summary.get("by_strategy_regime", []), use_container_width=True)

st.subheader("By Selection Reason")
st.dataframe(summary.get("by_reason", []), use_container_width=True)

with st.expander("Raw Outcomes"):
    st.dataframe(rows, use_container_width=True)
