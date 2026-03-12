from __future__ import annotations

from collections.abc import Sequence

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

    st.markdown(f"### {title}")
    with st.container(border=True):
        if not lines:
            st.caption(empty_message)
            return

        for index, line in enumerate(lines):
            if index:
                st.divider()
            st.caption(line)
