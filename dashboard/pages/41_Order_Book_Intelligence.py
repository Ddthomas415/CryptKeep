from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.order_book_intelligence import scan_order_book_pressure
from services.strategies.order_book_imbalance import signal_from_context as order_book_signal_from_context

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Order Book Intelligence")
st.caption("Order-book depth imbalance and pressure snapshot.")

col0, col1, col2 = st.columns([1, 1, 1])
with col0:
    venue = st.selectbox("Venue", ["coinbase", "kraken"], index=0)
with col1:
    depth = st.slider("Depth", min_value=5, max_value=25, value=10, step=5)
with col2:
    run_now = st.button("Load Order Book", width="stretch")

if "order_book_result" not in st.session_state:
    st.session_state["order_book_result"] = None

if run_now:
    with st.spinner("Loading order book intelligence..."):
        st.session_state["order_book_result"] = scan_order_book_pressure(
            venue=venue,
            depth=depth,
        )

result = st.session_state.get("order_book_result")

if result is None:
    st.info("Click 'Load Order Book' to fetch imbalance snapshots.")
    st.stop()

if not result.get("ok"):
    st.error("Order-book load failed.")
    st.stop()

rows = list(result.get("rows") or [])
signals = []
for row in rows:
    sig = order_book_signal_from_context(
        imbalance=float(row.get("imbalance") or 0.0),
    )
    signals.append({
        "symbol": row.get("symbol"),
        "imbalance": row.get("imbalance"),
        "pressure": row.get("pressure"),
        "action": sig.get("action"),
        "reason": sig.get("reason"),
        "spread_pct": row.get("spread_pct"),
    })

c0, c1, c2 = st.columns(3)
c0.metric("Venue", str(result.get("venue", "")))
c1.metric("Rows", len(rows))
c2.metric("Timestamp", str(result.get("ts", "")))

st.subheader("Order Book Signals")
st.dataframe(signals, use_container_width=True)

st.subheader("Buy Pressure")
st.dataframe(result.get("buy_pressure", []), use_container_width=True)

st.subheader("Sell Pressure")
st.dataframe(result.get("sell_pressure", []), use_container_width=True)

st.subheader("All Rows")
st.dataframe(rows, use_container_width=True)
