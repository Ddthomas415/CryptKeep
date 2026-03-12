from __future__ import annotations

import streamlit as st

from dashboard.components.header import render_page_header


render_page_header(
    "Markets",
    "Watchlist-first market intelligence view. Keep this page focused on assets and context.",
    badges=[{"label": "View", "value": "Research"}],
)

left, right = st.columns((1, 1.4))

with left:
    st.markdown("### Watchlist")
    st.dataframe(
        [
            {"asset": "BTC", "price": 84250.12, "change_24h_pct": 2.4, "signal": "watch"},
            {"asset": "ETH", "price": 4421.34, "change_24h_pct": 1.3, "signal": "monitor"},
            {"asset": "SOL", "price": 187.42, "change_24h_pct": 6.9, "signal": "research"},
        ],
        use_container_width=True,
        hide_index=True,
    )

with right:
    st.markdown("### Asset Detail")
    with st.container(border=True):
        st.markdown("#### SOL")
        st.caption("Price action + catalyst context")
        st.line_chart([180, 181, 183, 182, 184, 186, 187, 188, 187], use_container_width=True)
        st.caption("AI summary: momentum expansion with ecosystem headline support.")
