from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_kpi_cards
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar

st.set_page_config(page_title="CryptKeep", layout="wide", page_icon=":chart_with_upwards_trend:")

_st_button = st.button


def _disabled_button(label: str, *args, **kwargs):
    if isinstance(label, str) and "Start Live Bot" in label:
        kwargs["disabled"] = True
        return False
    return _st_button(label, *args, **kwargs)


st.button = _disabled_button

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

render_page_header(
    "Overview",
    "Summary-first workspace with advanced controls moved to Operations.",
    badges=[
        {"label": "Mode", "value": "Research Only"},
        {"label": "Risk", "value": "Safe"},
    ],
)

render_kpi_cards(
    [
        {"label": "Portfolio Value", "value": "$124,850", "delta": "+2.8%"},
        {"label": "PnL Today", "value": "+$2,145", "delta": "+1.7%"},
        {"label": "Active Signals", "value": "6", "delta": "2 high confidence"},
        {"label": "Bot Status", "value": "Running", "delta": "Automation enabled"},
    ]
)

col_signals, col_activity = st.columns((1.4, 1))

with col_signals:
    st.markdown("### Recent Signals")
    st.dataframe(
        [
            {"asset": "SOL", "thesis": "Momentum + catalyst", "confidence": 0.78, "status": "research"},
            {"asset": "BTC", "thesis": "Range breakout watch", "confidence": 0.66, "status": "watch"},
            {"asset": "ETH", "thesis": "Funding cooling", "confidence": 0.71, "status": "monitor"},
        ],
        use_container_width=True,
        hide_index=True,
    )

with col_activity:
    st.markdown("### Recent Activity")
    st.markdown("- Generated explanation for SOL")
    st.markdown("- Health check passed")
    st.markdown("- Listing logs refreshed")
    st.markdown("- Paper trade blocked by risk policy")
