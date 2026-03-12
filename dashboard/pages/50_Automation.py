from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

render_page_header(
    "Automation",
    "Control strategy behavior, schedules, and safe execution defaults.",
    badges=[{"label": "Execution", "value": "Disabled"}],
)

col_a, col_b = st.columns((1, 1))
with col_a:
    st.toggle("Enable automation", value=False, disabled=True)
    st.toggle("Dry run mode", value=True)
    st.selectbox("Default mode", ["research_only", "paper", "live_approval", "live_auto"], index=0)

with col_b:
    st.selectbox("Schedule", ["manual", "every 5 min", "every 15 min", "hourly"], index=0)
    st.selectbox("Marketplace routing", ["disabled", "paper only", "approval gated"], index=0)
    st.checkbox("Require approval for live actions", value=True)

st.info("Advanced execution controls are isolated in Operations and remain explicitly gated.")
