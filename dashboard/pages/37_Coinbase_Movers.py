from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.services.coinbase_movers import fetch_coinbase_movers


AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")


st.title("Coinbase Movers")
st.caption("Market-wide Coinbase spot movers using publicly available Coinbase data.")

col0, col1 = st.columns([1, 1])
with col0:
    limit = st.slider("Rows per section", min_value=10, max_value=100, value=25, step=5)
with col1:
    run_now = st.button("Fetch Coinbase Movers", width="stretch", key="coinbase_movers_run")

if "coinbase_movers_result" not in st.session_state:
    st.session_state["coinbase_movers_result"] = None

if run_now:
    with st.spinner("Fetching Coinbase market data..."):
        st.session_state["coinbase_movers_result"] = fetch_coinbase_movers(limit=limit)

result = st.session_state.get("coinbase_movers_result")

if result is None:
    st.info("Click 'Fetch Coinbase Movers' to load market-wide gainers and losers.")
    st.stop()

if not result.get("ok"):
    st.error("Failed to fetch Coinbase movers.")
    st.stop()

c0, c1, c2 = st.columns(3)
c0.metric("Scanned", int(result.get("scanned", 0)))
c1.metric("Errors", len(result.get("errors", [])))
c2.metric("Timestamp", str(result.get("ts", "")))

def _show(title: str, rows: list[dict]) -> None:
    st.subheader(title)
    if not rows:
        st.caption("No rows")
        return
    st.dataframe(rows, width="stretch")

_show("Top Gainers", result.get("gainers", []))
_show("Top Losers", result.get("losers", []))
_show("Most Active", result.get("most_active", []))
_show("Most Volatile", result.get("most_volatile", []))

with st.expander("All Ranked Markets"):
    st.dataframe(result.get("all", []), width="stretch")

with st.expander("Errors"):
    errs = result.get("errors", [])
    if errs:
        st.dataframe(errs, width="stretch")
    else:
        st.caption("No errors.")
