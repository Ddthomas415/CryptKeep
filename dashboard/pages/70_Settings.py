from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.forms import render_save_action
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
currency_options = ["USD", "EUR", "GBP", "USDC"]
mode_options = ["research_only", "paper", "live_approval", "live_auto"]
length_options = ["short", "normal", "detailed"]
tone_options = ["balanced", "concise", "detailed"]

timezone = str(general.get("timezone") or timezones[0])
default_currency = str(general.get("default_currency") or currency_options[0])
default_mode = str(general.get("default_mode") or mode_options[0])
explanation_length = str(ai.get("explanation_length") or length_options[1])
tone = str(ai.get("tone") or tone_options[0])
if timezone not in timezones:
    timezone = timezones[0]
if default_currency not in currency_options:
    currency_options = [default_currency, *[item for item in currency_options if item != default_currency]]
if default_mode not in mode_options:
    default_mode = mode_options[0]
if explanation_length not in length_options:
    explanation_length = length_options[1]
if tone not in tone_options:
    tone = tone_options[0]

watchlist_defaults = general.get("watchlist_defaults") if isinstance(general.get("watchlist_defaults"), list) else []
watchlist_defaults_text = ", ".join(str(item).strip() for item in watchlist_defaults if str(item).strip())

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
    default_currency_value = st.selectbox(
        "Default currency",
        currency_options,
        index=currency_options.index(default_currency),
    )
    default_mode_value = st.selectbox("Default mode", mode_options, index=mode_options.index(default_mode))
    startup_page_value = st.text_input("Startup page", value=str(general.get("startup_page") or "/dashboard"))
    watchlist_defaults_value = st.text_input("Watchlist defaults (comma separated)", value=watchlist_defaults_text)

with tab_notifications:
    email_value = st.checkbox("Email alerts", value=bool(notifications.get("email")))
    telegram_value = st.checkbox("Telegram alerts", value=bool(notifications.get("telegram")))
    discord_value = st.checkbox("Discord alerts", value=bool(notifications.get("discord")))
    webhook_value = st.checkbox("Webhook alerts", value=bool(notifications.get("webhook")))
    price_alerts_value = st.checkbox("Price alerts", value=bool(notifications.get("price_alerts", True)))
    news_alerts_value = st.checkbox("News alerts", value=bool(notifications.get("news_alerts", True)))
    catalyst_alerts_value = st.checkbox("Catalyst alerts", value=bool(notifications.get("catalyst_alerts", True)))
    risk_alerts_value = st.checkbox("Risk alerts", value=bool(notifications.get("risk_alerts")))
    approval_requests_value = st.checkbox(
        "Approval requests",
        value=bool(notifications.get("approval_requests", True)),
    )

with tab_ai:
    explanation_length_value = st.selectbox(
        "Explanation length",
        length_options,
        index=length_options.index(explanation_length),
    )
    tone_value = st.selectbox("Explanation tone", tone_options, index=tone_options.index(tone))
    show_evidence_value = st.checkbox("Show evidence", value=bool(ai.get("show_evidence", True)))
    show_confidence_value = st.checkbox("Show confidence", value=bool(ai.get("show_confidence", True)))
    include_archives_value = st.checkbox("Include archives", value=bool(ai.get("include_archives", True)))
    include_onchain_value = st.checkbox("Include on-chain", value=bool(ai.get("include_onchain", True)))
    include_social_value = st.checkbox("Include social", value=bool(ai.get("include_social", False)))
    allow_hypotheses_value = st.checkbox("Allow hypotheses", value=bool(ai.get("allow_hypotheses", True)))

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
        "default_currency": default_currency_value,
        "default_mode": default_mode_value,
        "startup_page": startup_page_value,
        "watchlist_defaults": [
            item.strip().upper()
            for item in watchlist_defaults_value.split(",")
            if item.strip()
        ],
    },
    "notifications": {
        **notifications,
        "email": email_value,
        "telegram": telegram_value,
        "discord": discord_value,
        "webhook": webhook_value,
        "price_alerts": price_alerts_value,
        "news_alerts": news_alerts_value,
        "catalyst_alerts": catalyst_alerts_value,
        "risk_alerts": risk_alerts_value,
        "approval_requests": approval_requests_value,
    },
    "ai": {
        **ai,
        "explanation_length": explanation_length_value,
        "tone": tone_value,
        "show_evidence": show_evidence_value,
        "show_confidence": show_confidence_value,
        "include_archives": include_archives_value,
        "include_onchain": include_onchain_value,
        "include_social": include_social_value,
        "allow_hypotheses": allow_hypotheses_value,
    },
    "security": {
        **security,
        "session_timeout_minutes": int(session_timeout_value),
        "secret_masking": secret_masking_value,
        "audit_export_allowed": audit_export_allowed_value,
    },
}

render_save_action(
    button_label="Save settings",
    button_key="ck_settings_save_button",
    session_key="ck_settings_save_result",
    payload=payload,
    save_fn=update_settings_view,
    success_message="Settings saved to the local API.",
    error_message="Settings save failed.",
)
