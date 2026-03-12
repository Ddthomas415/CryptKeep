from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.forms import render_save_action
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.view_data import get_automation_view, update_automation_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()
automation_view = get_automation_view()
default_mode_options = ["research_only", "paper", "live_approval", "live_auto"]
schedule_options = ["manual", "every 5 min", "every 15 min", "hourly"]
routing_options = ["disabled", "paper only", "approval gated"]

default_mode = str(automation_view.get("default_mode") or default_mode_options[0])
schedule = str(automation_view.get("schedule") or schedule_options[0])
routing = str(automation_view.get("marketplace_routing") or routing_options[0])
if default_mode not in default_mode_options:
    default_mode = default_mode_options[0]
if schedule not in schedule_options:
    schedule = schedule_options[0]
if routing not in routing_options:
    routing = routing_options[0]

render_page_header(
    "Automation",
    "Control strategy behavior, schedules, and safe execution defaults.",
    badges=[{"label": "Execution", "value": "Enabled" if automation_view.get("execution_enabled") else "Disabled"}],
)

col_a, col_b = st.columns((1, 1))
with col_a:
    enable_automation_value = st.toggle("Enable automation", value=bool(automation_view.get("execution_enabled")))
    dry_run_mode_value = st.toggle("Dry run mode", value=bool(automation_view.get("dry_run_mode")))
    default_mode_value = st.selectbox("Default mode", default_mode_options, index=default_mode_options.index(default_mode))

with col_b:
    schedule_value = st.selectbox("Schedule", schedule_options, index=schedule_options.index(schedule))
    routing_value = st.selectbox("Marketplace routing", routing_options, index=routing_options.index(routing))
    approval_required_value = st.checkbox(
        "Require approval for live actions",
        value=bool(automation_view.get("approval_required_for_live")),
    )

st.info("Advanced execution controls are isolated in Operations and remain explicitly gated.")
st.caption(
    f"Runtime config path: {automation_view.get('config_path')}  "
    f"(executor_mode={automation_view.get('executor_mode')}, live_enabled={automation_view.get('live_enabled')})"
)

payload = {
    "execution_enabled": enable_automation_value,
    "dry_run_mode": dry_run_mode_value,
    "default_mode": default_mode_value,
    "schedule": schedule_value,
    "marketplace_routing": routing_value,
    "approval_required_for_live": approval_required_value,
}

render_save_action(
    button_label="Save automation settings",
    button_key="ck_automation_save_button",
    session_key="ck_automation_save_result",
    payload=payload,
    save_fn=update_automation_view,
    success_message="Automation settings saved.",
    error_message="Automation settings save failed.",
)
