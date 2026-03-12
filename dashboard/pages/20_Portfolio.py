from __future__ import annotations

import streamlit as st

from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar

render_app_sidebar()

render_page_header(
    "Portfolio",
    "Position and allocation view for account-level decisions.",
    badges=[{"label": "Currency", "value": "USD"}],
)

metrics = st.columns(4)
metrics[0].metric("Total Value", "$124,850", "+2.8%")
metrics[1].metric("Cash", "$48,120")
metrics[2].metric("Unrealized PnL", "+$2,145")
metrics[3].metric("Exposure Used", "18.4%")

st.markdown("### Open Positions")
st.dataframe(
    [
        {"asset": "BTC", "side": "long", "size": 0.12, "entry": 80120, "mark": 84250, "pnl": 495.6},
        {"asset": "SOL", "side": "long", "size": 45.0, "entry": 173.4, "mark": 187.4, "pnl": 630.0},
    ],
    use_container_width=True,
    hide_index=True,
)
