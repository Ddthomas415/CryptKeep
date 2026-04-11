from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.market_intelligence import build_market_intelligence_snapshot

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Market Intelligence")
st.caption("Open interest, liquidation-risk scaffolding, and social sentiment placeholders.")

col0, col1 = st.columns([1, 1])
with col0:
    run_now = st.button("Load Market Intelligence", width="stretch")
with col1:
    futures_symbols = st.text_input("Futures symbols", value="BTC/USDT,ETH/USDT,SOL/USDT")

if "market_intel_result" not in st.session_state:
    st.session_state["market_intel_result"] = None

if run_now:
    with st.spinner("Loading market intelligence..."):
        futs = [x.strip() for x in futures_symbols.split(",") if x.strip()]
        st.session_state["market_intel_result"] = build_market_intelligence_snapshot(
            futures_symbols=futs,
            spot_symbols=["BTC/USD", "ETH/USD", "SOL/USD"],
        )

result = st.session_state.get("market_intel_result")

if result is None:
    st.info("Click 'Load Market Intelligence' to fetch the current snapshot.")
    st.stop()

if not result.get("ok"):
    st.error("Market intelligence load failed.")
    st.stop()

c0, c1 = st.columns(2)
c0.metric("Timestamp", str(result.get("ts", "")))
c1.metric("Sections", 3)

st.subheader("Open Interest")
st.dataframe((result.get("open_interest") or {}).get("rows", []), use_container_width=True)

st.subheader("Liquidation Risk")
st.dataframe((result.get("liquidation") or {}).get("rows", []), use_container_width=True)

st.subheader("Social Sentiment")
st.dataframe((result.get("social_sentiment") or {}).get("rows", []), use_container_width=True)
