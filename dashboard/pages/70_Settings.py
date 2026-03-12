from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.view_data import get_settings_view, update_settings_view

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
    timezone_value = st.selectbox("Timezone", timezones, index=timezones.index(timezone))
    default_mode_value = st.selectbox("Default mode", mode_options, index=mode_options.index(default_mode))
    startup_page_value = st.text_input("Startup page", value=str(general.get("startup_page") or "/dashboard"))

with tab_notifications:
    email_value = st.checkbox("Email alerts", value=bool(notifications.get("email")))
    telegram_value = st.checkbox("Telegram alerts", value=bool(notifications.get("telegram")))
    risk_alerts_value = st.checkbox("Risk alerts", value=bool(notifications.get("risk_alerts")))

with tab_ai:
    tone_value = st.selectbox("Explanation tone", tone_options, index=tone_options.index(tone))
    show_evidence_value = st.checkbox("Show evidence", value=bool(ai.get("show_evidence", True)))
    show_confidence_value = st.checkbox("Show confidence", value=bool(ai.get("show_confidence", True)))

with tab_security:
    session_timeout_value = st.number_input(
        "Session timeout (minutes)",
        min_value=5,
        max_value=240,
        value=int(security.get("session_timeout_minutes") or 60),
        step=5,
    )
    secret_masking_value = st.checkbox("Secret masking", value=bool(security.get("secret_masking", True)))
    audit_export_allowed_value = st.checkbox(
        "Audit export allowed",
        value=bool(security.get("audit_export_allowed", True)),
    )

payload = {
    "general": {
        **general,
        "timezone": timezone_value,
        "default_mode": default_mode_value,
        "startup_page": startup_page_value,
    },
    "notifications": {
        **notifications,
        "email": email_value,
        "telegram": telegram_value,
        "risk_alerts": risk_alerts_value,
    },
    "ai": {
        **ai,
        "tone": tone_value,
        "show_evidence": show_evidence_value,
        "show_confidence": show_confidence_value,
    },
    "security": {
        **security,
        "session_timeout_minutes": int(session_timeout_value),
        "secret_masking": secret_masking_value,
        "audit_export_allowed": audit_export_allowed_value,
    },
}

if st.button("Save settings", type="primary"):
    st.session_state["ck_settings_save_result"] = update_settings_view(payload)

save_result = st.session_state.get("ck_settings_save_result")
if isinstance(save_result, dict):
    if bool(save_result.get("ok")):
        st.success("Settings saved to the local API.")
    else:
        st.error(str(save_result.get("message") or "Settings save failed."))
