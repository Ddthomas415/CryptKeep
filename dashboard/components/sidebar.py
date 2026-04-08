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

OPERATOR_NAV_ITEMS: tuple[NavItem, ...] = (
    ("pages/65_Copilot_Reports.py", "Copilot Reports", "🤖"),
    ("pages/00_Operator.py", "Operator (Legacy)", "↩️"),
    ("pages/99_Legacy_UI.py", "Legacy UI", "🗃️"),
)

DEFAULT_BRAND_PILLS: tuple[str, ...] = (
    "Role Gated",
    "Workflow Shell",
)


def _page_link(path: str, *, label: str, icon: str) -> None:
    if hasattr(st, "page_link"):
        st.page_link(path, label=label, icon=icon)
    else:
        st.markdown(f"- {icon} {label}")


def _has_role(current_role: str, required_role: str) -> bool:
    order = {"VIEWER": 0, "OPERATOR": 1, "ADMIN": 2}
    cur = str(current_role or "VIEWER").strip().upper()
    req = str(required_role or "VIEWER").strip().upper()
    return order.get(cur, 0) >= order.get(req, 0)


def _default_secondary_nav_items() -> tuple[NavItem, ...]:
    session = st.session_state.get("cbp_auth_session")
    if not isinstance(session, dict):
        return ()
    role = str(session.get("role") or "VIEWER")
    if not _has_role(role, "OPERATOR"):
        return ()
    return OPERATOR_NAV_ITEMS


def render_app_sidebar(
    *,
    title: str = "CryptKeep",
    subtitle: str = "AI Trading Copilot",
    nav_items: Sequence[NavItem] = DEFAULT_NAV_ITEMS,
    brand_pills: Sequence[str] = DEFAULT_BRAND_PILLS,
    secondary_nav_items: Sequence[NavItem] | None = None,
    secondary_title: str = "Operator / Reports",
    show_legacy_note: bool = False,
) -> None:
    resolved_secondary_nav_items = (
        tuple(secondary_nav_items) if secondary_nav_items is not None else _default_secondary_nav_items()
    )
    rendered_pills = [
        f"<span class='ck-brand-pill'>{escape(str(item).strip())}</span>"
        for item in brand_pills
        if str(item).strip()
    ]
    pills_html = f"<div class='ck-brand-pills'>{''.join(rendered_pills)}</div>" if rendered_pills else ""

    with st.sidebar:
        st.markdown(
            f"""
            <div class="ck-brand">
              <div class="ck-brand-title">{escape(title)}</div>
              <div class="ck-brand-subtitle">{escape(subtitle)}</div>
              {pills_html}
            </div>
            <div class="ck-nav-label">Workspace</div>
            """,
            unsafe_allow_html=True,
        )
        for path, label, icon in nav_items:
            _page_link(path, label=label, icon=icon)
        if resolved_secondary_nav_items:
            st.markdown(f"<div class='ck-nav-label'>{escape(secondary_title)}</div>", unsafe_allow_html=True)
            for path, label, icon in resolved_secondary_nav_items:
                _page_link(path, label=label, icon=icon)
        if show_legacy_note:
            st.markdown(
                "<div class='ck-sidebar-note'>Legacy admin pages remain available for compatibility.</div>",
                unsafe_allow_html=True,
            )
