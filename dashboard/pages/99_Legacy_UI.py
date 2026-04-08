from __future__ import annotations

import streamlit as st
from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar

AUTH_STATE = require_authenticated_role("OPERATOR")
render_app_sidebar(
    brand_pills=("Operator Access", "Compatibility"),
    secondary_nav_items=(
        ("pages/00_Operator.py", "Operator (Legacy)", "↩️"),
        ("pages/99_Legacy_UI.py", "Legacy UI", "🗃️"),
    ),
)

render_page_header(
    "Legacy UI (Retired)",
    "The monolithic Streamlit dashboard is no longer loaded from this page.",
    badges=[
        {"label": "User", "value": str(AUTH_STATE.get("username") or "unknown")},
        {"label": "Role", "value": str(AUTH_STATE.get("role") or "OPERATOR")},
    ],
)

st.warning("Legacy UI is retired. Use Operations and the new workflow pages instead.")
st.caption("This page remains only as a compatibility marker for old bookmarks.")

if hasattr(st, "page_link"):
    st.page_link("pages/60_Operations.py", label="Open Operations", icon="🛠️")

with st.container(border=True):
    st.markdown("### Replacement pages")
    st.markdown("- Operations for system tools, logs, strategy controls, and recovery actions")
    st.markdown("- Overview for summary status and recent activity")
    st.markdown("- Portfolio, Signals, Trades, Automation, and Settings for focused workflow pages")
    st.info("If you need the historical monolithic dashboard again, restore it from git history into a separate page rather than importing it dynamically here.")
