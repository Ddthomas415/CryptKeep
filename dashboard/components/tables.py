from __future__ import annotations

from collections.abc import Sequence
from html import escape
from typing import Any

import streamlit as st


def render_table_section(
    title: str,
    rows: Sequence[dict[str, Any]] | None,
    *,
    empty_message: str = "No data available.",
) -> None:
    total = len(rows or [])
    st.markdown(
        f"""
        <div class="ck-section-head">
          <div class="ck-section-title">{escape(title)}</div>
          <div class="ck-section-meta">{total} row{'s' if total != 1 else ''}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        if not rows:
            st.info(empty_message)
            return
        st.dataframe(rows, use_container_width=True, hide_index=True)
