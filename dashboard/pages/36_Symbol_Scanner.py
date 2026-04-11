from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.services.symbol_scanner import run_symbol_scan

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Market Scanner")
st.caption("Read-only scanner powered by Coinbase market-wide movers data.")

col0, col1 = st.columns([1, 1])
with col0:
    run_now = st.button("Scan Coinbase Market", width="stretch", key="scanner_run")
with col1:
    rows_per_section = st.slider("Rows per section", min_value=10, max_value=50, value=20, step=5)

if "scanner_result" not in st.session_state:
    st.session_state["scanner_result"] = None

if run_now:
    with st.spinner("Scanning Coinbase market..."):
        st.session_state["scanner_result"] = run_symbol_scan(venue="coinbase", symbols=[])

result = st.session_state.get("scanner_result")

if result is None:
    st.info("Click 'Scan Coinbase Market' to scan all active Coinbase spot markets.")
    st.stop()

if not result.get("ok"):
    st.error("Market scan failed.")
    st.stop()

c0, c1, c2, c3 = st.columns(4)
c0.metric("Markets Scanned", int(result.get("scanned", 0)))
c1.metric("Errors", len(result.get("errors", [])))
c2.metric("Source", str(result.get("source", "")))
c3.metric("Timestamp", str(result.get("ts", "")))

def _show(title: str, rows: list[dict]) -> None:
    st.subheader(title)
    if not rows:
        st.caption("None found")
        return
    st.dataframe(rows[:rows_per_section], use_container_width=True)

_show("🔥 Hot Coins", result.get("hot", []))
_show("📈 Momentum", result.get("momentum", []))
_show("🚀 Top Gainers", result.get("gainers", []))
_show("📉 Top Losers", result.get("losers", []))
_show("🔊 Most Active", result.get("most_active", []))
_show("⚡ Most Volatile", result.get("most_volatile", []))

with st.expander("All Markets Ranked"):
    st.dataframe(result.get("all", []), use_container_width=True)

with st.expander("Errors"):
    errs = result.get("errors", [])
    if errs:
        st.dataframe(errs, use_container_width=True)
    else:
        st.caption("No errors.")
