from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_recommendations

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

render_page_header(
    "Signals",
    "AI recommendations, confidence, and evidence in one focused view.",
    badges=[{"label": "Mode", "value": "Research Only"}],
)

render_table_section(
    "Signals",
    get_recommendations(),
    empty_message="No recommendation data available.",
)

with st.expander("Why this signal?"):
    st.write("Signals are generated from market structure, catalyst extraction, and policy constraints.")
