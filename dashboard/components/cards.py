from __future__ import annotations

from collections.abc import Sequence

import streamlit as st


def render_kpi_cards(items: Sequence[dict[str, str]]) -> None:
    cards = list(items)
    if not cards:
        return

    cols = st.columns(len(cards))
    for col, item in zip(cols, cards, strict=False):
        with col:
            with st.container(border=True):
                st.caption(str(item.get("label") or ""))
                st.markdown(f"### {item.get('value') or '-'}")
                delta = str(item.get("delta") or "").strip()
                if delta:
                    st.caption(delta)
