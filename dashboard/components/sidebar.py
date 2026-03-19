from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

NavItem = tuple[str, str, str]


DEFAULT_NAV_ITEMS: tuple[NavItem, ...] = (
    ("pages/00_Home.py", "Home", "🏠"),
    ("pages/05_Help.py", "Help", "❓"),
    ("app.py", "Overview", "📋"),
    ("pages/10_Markets.py", "Markets", "📈"),
    ("pages/20_Portfolio.py", "Portfolio", "💼"),
    ("pages/30_Signals.py", "Signals", "🧠"),
    ("pages/35_Research.py", "Research", "🔬"),
    ("pages/40_Trades.py", "Trades", "🔁"),
    ("pages/50_Automation.py", "Automation", "⚙️"),
    ("pages/60_Operations.py", "Operations", "🛠️"),
    ("pages/70_Settings.py", "Settings", "🔒"),
)


def _page_link(path: str, *, label: str, icon: str) -> None:
    if hasattr(st, "page_link"):
        st.page_link(path, label=label, icon=icon)
    else:
        st.markdown(f"- {icon} {label}")


def render_app_sidebar(
    *,
    title: str = "CryptKeep",
    subtitle: str = "AI Trading Copilot",
    nav_items: Sequence[NavItem] = DEFAULT_NAV_ITEMS,
    secondary_nav_items: Sequence[NavItem] | None = None,
    secondary_title: str = "Admin / Legacy",
    show_legacy_note: bool = False,
) -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="ck-brand">
              <div class="ck-brand-title">{escape(title)}</div>
              <div class="ck-brand-subtitle">{escape(subtitle)}</div>
              <div class="ck-brand-pills">
                <span class="ck-brand-pill">Research Only</span>
                <span class="ck-brand-pill">Paper Safe</span>
              </div>
            </div>
            <div class="ck-nav-label">Workspace</div>
            """,
            unsafe_allow_html=True,
        )
        for path, label, icon in nav_items:
            _page_link(path, label=label, icon=icon)
        if secondary_nav_items:
            st.markdown(f"<div class='ck-nav-label'>{escape(secondary_title)}</div>", unsafe_allow_html=True)
            for path, label, icon in secondary_nav_items:
                _page_link(path, label=label, icon=icon)
        if show_legacy_note:
            st.markdown(
                "<div class='ck-sidebar-note'>Legacy admin pages remain available for compatibility.</div>",
                unsafe_allow_html=True,
            )
