from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header

AUTH_STATE = require_authenticated_role("OPERATOR")

render_page_header(
    "Operator (Legacy)",
    "This compatibility page forwards Operator users to the new Operations workspace.",
    badges=[
        {"label": "User", "value": str(AUTH_STATE.get("username") or "unknown")},
        {"label": "Role", "value": str(AUTH_STATE.get("role") or "OPERATOR")},
    ],
)

st.warning("Operator tools have moved to the Operations page.")
st.caption("Use this page only as a compatibility entry point for old bookmarks.")

if hasattr(st, "switch_page"):
    if st.button("Open Operations", use_container_width=True, type="primary"):
        st.switch_page("dashboard/pages/60_Operations.py")
else:
    st.page_link("dashboard/pages/60_Operations.py", label="Open Operations", icon="🛠️")

st.markdown("### Moved to Operations")
st.markdown("- System tools (preflight, supervisor, service controls)")
st.markdown("- Service logs and action output")
st.markdown("- Order blocked inspector")
st.markdown("- Strategy and parity backtest controls")
st.markdown("- Safety and recovery tooling")
