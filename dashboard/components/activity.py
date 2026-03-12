from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st


def normalize_activity_items(items: Sequence[object] | None, *, limit: int = 6) -> list[str]:
    lines: list[str] = []
    for item in items or []:
        text = str(item or "").strip()
        if text:
            lines.append(text)
        if len(lines) >= max(int(limit), 0):
            break
    return lines


def render_activity_panel(
    items: Sequence[object] | None,
    *,
    title: str = "Recent Activity",
    empty_message: str = "No recent activity available.",
    limit: int = 6,
) -> None:
    lines = normalize_activity_items(items, limit=limit)

    st.markdown(
        f"""
        <div class="ck-section-head">
          <div class="ck-section-title">{escape(title)}</div>
          <div class="ck-section-meta">{len(lines)} item{'s' if len(lines) != 1 else ''}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        if not lines:
            st.caption(empty_message)
            return

        st.markdown(
            "<div class='ck-activity-list'>"
            + "".join(f"<div class='ck-activity-item'>{escape(line)}</div>" for line in lines)
            + "</div>",
            unsafe_allow_html=True,
        )
