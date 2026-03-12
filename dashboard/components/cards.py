from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st


def render_kpi_cards(items: Sequence[dict[str, str]]) -> None:
    cards = list(items)
    if not cards:
        return

    cols = st.columns(len(cards))
    for col, item in zip(cols, cards, strict=False):
        with col:
            with st.container(border=True):
                label = str(item.get("label") or "")
                value = str(item.get("value") or "-")
                delta = str(item.get("delta") or "").strip()
                delta_html = f"<div class='ck-kpi-delta'>{escape(delta)}</div>" if delta else ""
                st.markdown(
                    f"""
                    <div class="ck-kpi-card">
                      <div class="ck-kpi-label">{escape(label)}</div>
                      <div class="ck-kpi-value">{escape(value)}</div>
                      {delta_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
