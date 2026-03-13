from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_kpi_cards, render_prompt_actions
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_portfolio_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_portfolio_position_summary
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_portfolio_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()
portfolio_view = get_portfolio_view()
portfolio = portfolio_view.get("portfolio") if isinstance(portfolio_view.get("portfolio"), dict) else {}
positions = portfolio_view.get("positions") if isinstance(portfolio_view.get("positions"), list) else []
currency = str(portfolio_view.get("currency") or "USD")

render_page_header(
    "Portfolio",
    "Position and allocation view for account-level decisions.",
    badges=[{"label": "Currency", "value": currency}],
)

render_kpi_cards(build_portfolio_kpis(portfolio=portfolio, positions=positions))
render_prompt_actions(
    title="Ask Copilot",
    prompts=[
        "Summarize portfolio risk",
        "Which holding is strongest right now?",
        "What changed in positions today?",
    ],
    key_prefix="portfolio_copilot",
)

summary_col, table_col = st.columns((1, 1.4))

with summary_col:
    render_portfolio_position_summary(positions)

with table_col:
    render_table_section(
        "Open Positions",
        positions,
        empty_message="No open positions.",
    )
