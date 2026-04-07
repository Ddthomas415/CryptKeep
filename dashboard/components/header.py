from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from dashboard.styles.theme import inject_theme


def render_page_header(title: str, subtitle: str = "", badges: Sequence[dict[str, str]] | None = None) -> None:
    if not st.session_state.get("_ck_theme_injected"):
        inject_theme()
        st.session_state["_ck_theme_injected"] = True

    left, right = st.columns((2.4, 1))

    with left:
        subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
        st.markdown(
            f"""
            <div class="ck-page-intro">
              <h1>{escape(title)}</h1>
              {subtitle_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        with st.container():
            rendered_badges: list[str] = []
        for badge in badges or []:
            label = str(badge.get("label") or "").strip()
            value = str(badge.get("value") or "").strip()
            if not (label or value):
                continue
            rendered_badges.append(
                f"""
                <div class="ck-badge">
                  <span class="ck-badge-label">{escape(label or "Status")}</span>
                  <span class="ck-badge-value">{escape(value or "-")}</span>
                </div>
                """
            )
        if rendered_badges:
            st.markdown(
                f"<div class='ck-badge-row'>{''.join(rendered_badges)}</div>",
                unsafe_allow_html=True,
            )
