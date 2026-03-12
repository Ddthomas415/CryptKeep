from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
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

metrics = st.columns(4)
metrics[0].metric("Total Value", f"${float(portfolio.get('total_value') or 0.0):,.2f}")
metrics[1].metric("Cash", f"${float(portfolio.get('cash') or 0.0):,.2f}")
metrics[2].metric("Unrealized PnL", f"${float(portfolio.get('unrealized_pnl') or 0.0):,.2f}")
metrics[3].metric("Exposure Used", f"{float(portfolio.get('exposure_used_pct') or 0.0):.1f}%")

st.markdown("### Open Positions")
st.dataframe(
    positions,
    use_container_width=True,
    hide_index=True,
)
