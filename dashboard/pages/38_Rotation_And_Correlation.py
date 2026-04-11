from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.rotation_engine import build_rotation_candidates

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Rotation & Correlation")
st.caption("Rotation candidates from market scanner hot list. Correlation diversification comes next once local OHLCV is wired.")

col0, col1 = st.columns([1, 1])
with col0:
    top_n = st.slider("Top candidates", min_value=5, max_value=20, value=10, step=1)
with col1:
    run_now = st.button("Build Rotation List", width="stretch")

if "rotation_result" not in st.session_state:
    st.session_state["rotation_result"] = None

if run_now:
    with st.spinner("Building rotation candidates..."):
        st.session_state["rotation_result"] = build_rotation_candidates(top_n=top_n)

result = st.session_state.get("rotation_result")

if result is None:
    st.info("Click 'Build Rotation List' to build the current rotation list from scanner intelligence.")
    st.stop()

if not result.get("ok"):
    st.error("Rotation build failed.")
    st.stop()

c0, c1, c2 = st.columns(3)
c0.metric("Scanned", int(result.get("scanned", 0)))
c1.metric("Selected", len(result.get("selected", [])))
c2.metric("Timestamp", str(result.get("ts", "")))

mr = result.get("market_regime") or {}
if mr:
    m0, m1, m2 = st.columns(3)
    m0.metric("Market Regime", str(mr.get("regime", "unknown")))
    m1.metric("Fear & Greed", str(mr.get("fg_value", mr.get("fear_greed", {}).get("value", ""))))
    m2.metric("Market Signal", str(mr.get("signal", "neutral")))

st.subheader("Selected Symbols")
st.write(result.get("selected", []))

st.subheader("Rotation Candidates")
st.dataframe(result.get("rows", []), use_container_width=True)
