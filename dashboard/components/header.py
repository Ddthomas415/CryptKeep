from __future__ import annotations

from collections.abc import Sequence

import streamlit as st


def render_page_header(title: str, subtitle: str = "", badges: Sequence[dict[str, str]] | None = None) -> None:
    left, right = st.columns((2.4, 1))

    with left:
        st.title(title)
        if subtitle:
            st.caption(subtitle)

    with right:
        for badge in badges or []:
            label = str(badge.get("label") or "").strip()
            value = str(badge.get("value") or "").strip()
            if not (label or value):
                continue
            text = f"{label}: {value}" if label else value
            st.markdown(f"<span class='ck-badge'>{text}</span>", unsafe_allow_html=True)
