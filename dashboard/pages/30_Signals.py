from __future__ import annotations

import streamlit as st

from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar

render_app_sidebar()

render_page_header(
    "Signals",
    "AI recommendations, confidence, and evidence in one focused view.",
    badges=[{"label": "Mode", "value": "Research Only"}],
)

st.dataframe(
    [
        {
            "asset": "SOL",
            "signal": "buy",
            "confidence": 0.78,
            "summary": "Momentum + catalyst alignment",
            "evidence": "spot volume, ecosystem releases",
        },
        {
            "asset": "BTC",
            "signal": "hold",
            "confidence": 0.66,
            "summary": "Range breakout not confirmed",
            "evidence": "weak continuation volume",
        },
    ],
    use_container_width=True,
    hide_index=True,
)

with st.expander("Why this signal?"):
    st.write("Signals are generated from market structure, catalyst extraction, and policy constraints.")
