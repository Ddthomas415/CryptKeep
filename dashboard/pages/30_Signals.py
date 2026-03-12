from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.view_data import get_recommendations

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

render_page_header(
    "Signals",
    "AI recommendations, confidence, and evidence in one focused view.",
    badges=[{"label": "Mode", "value": "Research Only"}],
)

st.dataframe(
    get_recommendations(),
    use_container_width=True,
    hide_index=True,
)

with st.expander("Why this signal?"):
    st.write("Signals are generated from market structure, catalyst extraction, and policy constraints.")
