from __future__ import annotations

import sys
from types import SimpleNamespace

from dashboard.styles import theme_enhanced


def test_inject_enhanced_theme_sets_shared_flag_once(monkeypatch):
    calls: list[str] = []

    fake_st = SimpleNamespace(
        session_state={},
        markdown=lambda text, unsafe_allow_html=False: calls.append(str(text)),
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)

    theme_enhanced.inject_enhanced_theme()
    theme_enhanced.inject_enhanced_theme()

    assert fake_st.session_state["_ck_theme_injected"] is True
    assert len(calls) == 1
    assert '[data-testid="stHeader"]' in calls[0]
    assert '[data-testid="stToolbar"]' in calls[0]
    assert '[data-testid="stAppDeployButton"]' in calls[0]
    assert '[data-testid="stSidebarNavItems"]' in calls[0]
    assert '[data-testid="stSidebarNavViewButton"]' in calls[0]


def test_inject_enhanced_theme_force_reapplies_css(monkeypatch):
    calls: list[str] = []

    fake_st = SimpleNamespace(
        session_state={},
        markdown=lambda text, unsafe_allow_html=False: calls.append(str(text)),
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)

    theme_enhanced.inject_enhanced_theme()
    theme_enhanced.inject_enhanced_theme(force=True)

    assert fake_st.session_state["_ck_theme_injected"] is True
    assert len(calls) == 2
