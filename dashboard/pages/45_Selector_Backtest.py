from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.backtest.selector_backtest import backtest_selector_comparison

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Selector Backtest")
st.caption("Compare old hot-score selection against the new composite ranker.")

col0, col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1, 1])
with col0:
    top_n = st.slider("Top N", min_value=3, max_value=15, value=8, step=1)
with col1:
    max_abs_corr = st.slider("Max abs correlation", min_value=0.30, max_value=0.95, value=0.85, step=0.05)
with col2:
    momentum_mult = st.slider("Momentum weight", min_value=0.5, max_value=4.0, value=2.0, step=0.5)
with col3:
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
with col4:
    forward_bars = st.slider("Forward bars", min_value=1, max_value=24, value=1, step=1)
with col5:
    run_now = st.button("Run Selector Backtest", width="stretch")

if "selector_backtest_result" not in st.session_state:
    st.session_state["selector_backtest_result"] = None

if run_now:
    with st.spinner("Comparing selectors..."):
        st.session_state["selector_backtest_result"] = backtest_selector_comparison(
            top_n=top_n,
            max_abs_corr=max_abs_corr,
            ranking_config={
                "momentum_mult": momentum_mult,
            },
            timeframe=timeframe,
            forward_bars=forward_bars,
        )

result = st.session_state.get("selector_backtest_result")

if result is None:
    st.info("Click 'Run Selector Backtest' to compare selection logic.")
    st.stop()

baseline = (result.get("baseline") or {})
composite = (result.get("composite") or {})
delta = result.get("delta") or {}

st.caption(f"Forward window: {result.get('forward_bars')} bar(s) on {result.get('timeframe')}")

c0, c1, c2 = st.columns(3)
c0.metric("Δ Avg Return %", float(delta.get("avg_return_pct", 0.0)))
c1.metric("Δ Hit Rate", float(delta.get("hit_rate", 0.0)))
c2.metric("Δ Total Return %", float(delta.get("total_return_pct", 0.0)))

st.subheader("Baseline Summary")
st.json(baseline.get("summary") or {})

st.subheader("Composite Summary")
st.json(composite.get("summary") or {})

st.subheader("Baseline Symbols")
st.write(baseline.get("symbols") or [])

st.subheader("Composite Symbols")
st.write(composite.get("symbols") or [])

st.subheader("Baseline Rows")
st.dataframe(baseline.get("rows", []), use_container_width=True)

st.subheader("Composite Rows")
st.dataframe(composite.get("rows", []), use_container_width=True)
