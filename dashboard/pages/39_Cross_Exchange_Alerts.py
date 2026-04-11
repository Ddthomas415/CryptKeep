from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.cross_exchange_discrepancy import scan_cross_exchange_discrepancies

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Cross-Exchange Alerts")
st.caption("Spot price discrepancies across venues.")

col0, col1 = st.columns([1, 1])
with col0:
    min_discrepancy_pct = st.slider("Min discrepancy %", min_value=0.1, max_value=3.0, value=0.5, step=0.1)
with col1:
    run_now = st.button("Scan Cross-Exchange Alerts", width="stretch")

if "cross_exchange_result" not in st.session_state:
    st.session_state["cross_exchange_result"] = None

if run_now:
    with st.spinner("Scanning venues..."):
        st.session_state["cross_exchange_result"] = scan_cross_exchange_discrepancies(
            min_discrepancy_pct=min_discrepancy_pct
        )

result = st.session_state.get("cross_exchange_result")

if result is None:
    st.info("Click 'Scan Cross-Exchange Alerts' to compare venues.")
    st.stop()

if not result.get("ok"):
    st.error("Cross-exchange scan failed.")
    st.stop()

c0, c1, c2 = st.columns(3)
c0.metric("Scanned Symbols", int(result.get("scanned_symbols", 0)))
c1.metric("Alerts", len(result.get("rows", [])))
c2.metric("Timestamp", str(result.get("ts", "")))

st.dataframe(result.get("rows", []), use_container_width=True)
