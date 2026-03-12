from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.view_data import get_trades_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()
trades_view = get_trades_view()
pending_approvals = (
    trades_view.get("pending_approvals") if isinstance(trades_view.get("pending_approvals"), list) else []
)
recent_fills = trades_view.get("recent_fills") if isinstance(trades_view.get("recent_fills"), list) else []
approval_required = bool(trades_view.get("approval_required", True))

render_page_header(
    "Trades",
    "Approvals, orders, and fills with execution state clarity.",
    badges=[{"label": "Safety", "value": "Approval Required" if approval_required else "Auto Approved"}],
)

st.markdown("### Pending Approvals")
st.dataframe(
    pending_approvals,
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Recent Fills")
st.dataframe(
    recent_fills,
    use_container_width=True,
    hide_index=True,
)
