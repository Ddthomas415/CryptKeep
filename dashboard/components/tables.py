from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st


def render_table_section(
    title: str,
    rows: Sequence[dict[str, Any]] | None,
    *,
    empty_message: str = "No data available.",
) -> None:
    st.markdown(f"### {title}")
    if not rows:
        st.info(empty_message)
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)
