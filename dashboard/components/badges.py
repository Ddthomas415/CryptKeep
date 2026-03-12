from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st


def badge_html(text: str, *, tone: str = "default") -> str:
    safe_tone = escape(tone.strip().lower() or "default")
    safe_text = escape(text.strip())
    return f"<span class='ck-mini-badge ck-mini-badge--{safe_tone}'>{safe_text}</span>"


def badge_row_html(items: Sequence[dict[str, str] | str] | None) -> str:
    parts: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            tone = str(item.get("tone") or "default").strip()
        else:
            text = str(item or "").strip()
            tone = "default"
        if not text:
            continue
        parts.append(badge_html(text, tone=tone))
    return f"<div class='ck-mini-badge-row'>{''.join(parts)}</div>" if parts else ""


def render_badge_row(items: Sequence[dict[str, str] | str] | None) -> None:
    html = badge_row_html(items)
    if html:
        st.markdown(html, unsafe_allow_html=True)
