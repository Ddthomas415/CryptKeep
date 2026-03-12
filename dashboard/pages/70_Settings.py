from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

render_page_header(
    "Settings",
    "General, notifications, AI, and security preferences.",
    badges=[{"label": "Profile", "value": "Default Workspace"}],
)

tab_general, tab_notifications, tab_ai, tab_security = st.tabs(
    ["General", "Notifications", "AI", "Security"]
)

with tab_general:
    st.selectbox("Timezone", ["America/New_York", "UTC"], index=0)
    st.selectbox("Default mode", ["research_only", "paper", "live_approval", "live_auto"], index=0)
    st.text_input("Startup page", value="Overview")

with tab_notifications:
    st.checkbox("Email alerts", value=False)
    st.checkbox("Telegram alerts", value=True)
    st.checkbox("Risk alerts", value=True)

with tab_ai:
    st.selectbox("Explanation tone", ["balanced", "concise", "detailed"], index=0)
    st.checkbox("Show evidence", value=True)
    st.checkbox("Show confidence", value=True)

with tab_security:
    st.number_input("Session timeout (minutes)", min_value=5, max_value=240, value=60, step=5)
    st.checkbox("Secret masking", value=True)
    st.checkbox("Audit export allowed", value=True)

st.button("Save settings", type="primary")
