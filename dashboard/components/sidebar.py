from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

NavItem = tuple[str, str, str]


DEFAULT_NAV_ITEMS: tuple[NavItem, ...] = (
    ("dashboard/app.py", "Overview", "🏠"),
    ("dashboard/pages/10_Markets.py", "Markets", "📈"),
    ("dashboard/pages/20_Portfolio.py", "Portfolio", "💼"),
    ("dashboard/pages/30_Signals.py", "Signals", "🧠"),
    ("dashboard/pages/40_Trades.py", "Trades", "🔁"),
    ("dashboard/pages/50_Automation.py", "Automation", "⚙️"),
    ("dashboard/pages/60_Operations.py", "Operations", "🛠️"),
    ("dashboard/pages/70_Settings.py", "Settings", "🔒"),
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
    show_legacy_note: bool = True,
) -> None:
    with st.sidebar:
        st.markdown(f"## {title}")
        st.caption(subtitle)
        st.markdown("---")
        for path, label, icon in nav_items:
            _page_link(path, label=label, icon=icon)
        st.markdown("---")
        if show_legacy_note:
            st.caption("Legacy admin pages remain available for compatibility.")
