from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.view_data import get_settings_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()
settings_view = get_settings_view()
general = settings_view.get("general") if isinstance(settings_view.get("general"), dict) else {}
notifications = settings_view.get("notifications") if isinstance(settings_view.get("notifications"), dict) else {}
ai = settings_view.get("ai") if isinstance(settings_view.get("ai"), dict) else {}
security = settings_view.get("security") if isinstance(settings_view.get("security"), dict) else {}

timezones = ["America/New_York", "UTC"]
mode_options = ["research_only", "paper", "live_approval", "live_auto"]
tone_options = ["balanced", "concise", "detailed"]

timezone = str(general.get("timezone") or timezones[0])
default_mode = str(general.get("default_mode") or mode_options[0])
tone = str(ai.get("tone") or tone_options[0])
if timezone not in timezones:
    timezone = timezones[0]
if default_mode not in mode_options:
    default_mode = mode_options[0]
if tone not in tone_options:
    tone = tone_options[0]

render_page_header(
    "Settings",
    "General, notifications, AI, and security preferences.",
    badges=[{"label": "Profile", "value": "Default Workspace"}],
)

tab_general, tab_notifications, tab_ai, tab_security = st.tabs(
    ["General", "Notifications", "AI", "Security"]
)

with tab_general:
    st.selectbox("Timezone", timezones, index=timezones.index(timezone), disabled=True)
    st.selectbox("Default mode", mode_options, index=mode_options.index(default_mode), disabled=True)
    st.text_input("Startup page", value=str(general.get("startup_page") or "/dashboard"), disabled=True)

with tab_notifications:
    st.checkbox("Email alerts", value=bool(notifications.get("email")), disabled=True)
    st.checkbox("Telegram alerts", value=bool(notifications.get("telegram")), disabled=True)
    st.checkbox("Risk alerts", value=bool(notifications.get("risk_alerts")), disabled=True)

with tab_ai:
    st.selectbox("Explanation tone", tone_options, index=tone_options.index(tone), disabled=True)
    st.checkbox("Show evidence", value=bool(ai.get("show_evidence", True)), disabled=True)
    st.checkbox("Show confidence", value=bool(ai.get("show_confidence", True)), disabled=True)

with tab_security:
    st.number_input(
        "Session timeout (minutes)",
        min_value=5,
        max_value=240,
        value=int(security.get("session_timeout_minutes") or 60),
        step=5,
        disabled=True,
    )
    st.checkbox("Secret masking", value=bool(security.get("secret_masking", True)), disabled=True)
    st.checkbox("Audit export allowed", value=bool(security.get("audit_export_allowed", True)), disabled=True)

st.button("Save settings", type="primary", disabled=True)
st.caption("Settings edits remain read-only in the Streamlit shell. Persisted updates live in the API application.")
