from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.view_data import get_automation_view

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
    st.toggle("Enable automation", value=bool(automation_view.get("execution_enabled")), disabled=True)
    st.toggle("Dry run mode", value=bool(automation_view.get("dry_run_mode")), disabled=True)
    st.selectbox("Default mode", default_mode_options, index=default_mode_options.index(default_mode), disabled=True)

with col_b:
    st.selectbox("Schedule", schedule_options, index=schedule_options.index(schedule), disabled=True)
    st.selectbox("Marketplace routing", routing_options, index=routing_options.index(routing), disabled=True)
    st.checkbox("Require approval for live actions", value=bool(automation_view.get("approval_required_for_live")), disabled=True)

st.info("Advanced execution controls are isolated in Operations and remain explicitly gated.")
st.caption("This Streamlit page is a read-only control summary until persistence-backed automation settings are wired.")
