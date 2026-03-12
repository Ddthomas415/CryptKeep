from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from dashboard.components.badges import badge_row_html


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


def render_feature_hero(
    *,
    eyebrow: str,
    title: str,
    summary: str,
    body: str = "",
    badges: Sequence[dict[str, str] | str] | None = None,
    metrics: Sequence[dict[str, str]] | None = None,
    aside_title: str = "",
    aside_lines: Sequence[str] | None = None,
) -> None:
    badge_markup = badge_row_html(badges)
    safe_body = escape(body.strip()) if body.strip() else ""

    with st.container(border=True):
        left, right = st.columns((1.45, 0.85))

        with left:
            body_html = f"<p class='ck-hero-body'>{safe_body}</p>" if safe_body else ""
            st.markdown(
                f"""
                <div class="ck-hero">
                  <div class="ck-hero-eyebrow">{escape(eyebrow)}</div>
                  <div class="ck-hero-title">{escape(title)}</div>
                  <p class="ck-hero-summary">{escape(summary)}</p>
                  {badge_markup}
                  {body_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            metric_items = list(metrics or [])
            if metric_items:
                metric_cols = st.columns(len(metric_items))
                for col, item in zip(metric_cols, metric_items, strict=False):
                    with col:
                        with st.container(border=True):
                            st.caption(str(item.get("label") or ""))
                            st.markdown(f"**{str(item.get('value') or '-')}**")
                            delta = str(item.get("delta") or "").strip()
                            if delta:
                                st.caption(delta)

        with right:
            if aside_title or aside_lines:
                lines_markup = "".join(
                    f"<li>{escape(str(line).strip())}</li>"
                    for line in (aside_lines or [])
                    if str(line).strip()
                )
                st.markdown(
                    f"""
                    <div class="ck-note-card">
                      <div class="ck-note-card-title">{escape(aside_title or "AI Copilot")}</div>
                      <ul class="ck-note-card-list">{lines_markup}</ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
