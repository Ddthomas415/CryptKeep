from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.activity import render_activity_panel
from dashboard.components.asset_detail import render_focus_summary
from dashboard.components.cards import render_kpi_cards
from dashboard.components.focus_selector import render_focus_selector
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_overview_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_overview_status_summary
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_overview_view

st.set_page_config(page_title="CryptKeep", layout="wide", page_icon=":chart_with_upwards_trend:")

_st_button = st.button


def _disabled_button(label: str, *args, **kwargs):
    if isinstance(label, str) and "Start Live Bot" in label:
        kwargs["disabled"] = True
        return False
    return _st_button(label, *args, **kwargs)


st.button = _disabled_button

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

overview_view = get_overview_view()
signal_rows = overview_view.get("signals") if isinstance(overview_view.get("signals"), list) else []
detail = overview_view.get("detail") if isinstance(overview_view.get("detail"), dict) else {}
focus_asset, default_asset, _focus_options = render_focus_selector(
    signal_rows,
    label="Focus signal",
    selected_asset=str(overview_view.get("selected_asset") or ""),
    fallback_asset="SOL",
    key="overview_selected_signal",
)
if focus_asset != default_asset:
    overview_view = get_overview_view(selected_asset=focus_asset)
    signal_rows = overview_view.get("signals") if isinstance(overview_view.get("signals"), list) else signal_rows
    detail = overview_view.get("detail") if isinstance(overview_view.get("detail"), dict) else detail

summary = overview_view.get("summary") if isinstance(overview_view.get("summary"), dict) else {}
portfolio = summary.get("portfolio") if isinstance(summary.get("portfolio"), dict) else {}
recent_activity = overview_view.get("recent_activity") if isinstance(overview_view.get("recent_activity"), list) else []

mode = str(summary.get("mode") or "research_only")
risk_status = str(summary.get("risk_status") or "safe")
execution_enabled = bool(summary.get("execution_enabled", False))

render_page_header(
    "Overview",
    "Summary-first workspace with advanced controls moved to Operations.",
    badges=[
        {"label": "Mode", "value": mode.replace("_", " ").title()},
        {"label": "Risk", "value": risk_status.title()},
    ],
)

render_kpi_cards(build_overview_kpis(portfolio=portfolio, signal_count=len(signal_rows), execution_enabled=execution_enabled))

col_signals, col_activity = st.columns((1.4, 1))

with col_signals:
    render_table_section(
        "Recent Signals",
        signal_rows,
        empty_message="No recent signals available.",
    )
    render_focus_summary(detail)

with col_activity:
    render_overview_status_summary(summary)
    render_activity_panel(recent_activity)
