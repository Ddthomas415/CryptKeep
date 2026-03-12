from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

render_page_header(
    "Trades",
    "Approvals, orders, and fills with execution state clarity.",
    badges=[{"label": "Safety", "value": "Approval Required"}],
)

st.markdown("### Pending Approvals")
st.dataframe(
    [
        {"id": "rec_1", "asset": "SOL", "side": "buy", "risk_size_pct": 1.5, "status": "pending_review"},
    ],
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Recent Fills")
st.dataframe(
    [
        {"ts": "2026-03-11T12:20:00Z", "asset": "BTC", "side": "buy", "qty": 0.01, "price": 83500.0},
        {"ts": "2026-03-11T11:05:00Z", "asset": "ETH", "side": "sell", "qty": 0.3, "price": 4390.0},
    ],
    use_container_width=True,
    hide_index=True,
)
