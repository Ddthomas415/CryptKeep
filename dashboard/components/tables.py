from __future__ import annotations

from collections.abc import Sequence
from html import escape
from typing import Any

import streamlit as st


def render_table_section(
    title: str,
    rows: Sequence[dict[str, Any]] | None,
    *,
    subtitle: str = "",
    empty_message: str = "No data available.",
) -> None:
    total = len(rows or [])
    subtitle_html = (
        f"<div class='ck-section-subtitle'>{escape(subtitle)}</div>"
        if subtitle.strip()
        else ""
    )
    st.markdown(
        f"""
        <div class="ck-section-head">
          <div>
            <div class="ck-section-title">{escape(title)}</div>
            {subtitle_html}
          </div>
          <div class="ck-section-meta">{total} row{'s' if total != 1 else ''}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        if not rows:
            st.info(empty_message)
            return
        st.dataframe(rows, width="stretch", hide_index=True)
