from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_kpi_cards
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.view_data import get_dashboard_summary, get_recent_activity, get_recommendations

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

summary = get_dashboard_summary()
portfolio = summary.get("portfolio") if isinstance(summary.get("portfolio"), dict) else {}
recommendations = get_recommendations()
recent_activity = get_recent_activity()

mode = str(summary.get("mode") or "research_only")
risk_status = str(summary.get("risk_status") or "safe")
execution_enabled = bool(summary.get("execution_enabled", False))

total_value = float(portfolio.get("total_value") or 0.0)
cash_value = float(portfolio.get("cash") or 0.0)
unrealized_pnl = float(portfolio.get("unrealized_pnl") or 0.0)

render_page_header(
    "Overview",
    "Summary-first workspace with advanced controls moved to Operations.",
    badges=[
        {"label": "Mode", "value": mode.replace("_", " ").title()},
        {"label": "Risk", "value": risk_status.title()},
    ],
)

render_kpi_cards(
    [
        {"label": "Portfolio Value", "value": f"${total_value:,.2f}", "delta": f"Cash ${cash_value:,.2f}"},
        {"label": "Unrealized PnL", "value": f"${unrealized_pnl:,.2f}", "delta": "Live mark-to-market"},
        {"label": "Active Signals", "value": str(len(recommendations)), "delta": "Recommendation set"},
        {
            "label": "Bot Status",
            "value": "Running" if execution_enabled else "Research Only",
            "delta": "Automation enabled" if execution_enabled else "Execution disabled",
        },
    ]
)

col_signals, col_activity = st.columns((1.4, 1))

with col_signals:
    st.markdown("### Recent Signals")
    signal_rows = [
        {
            "asset": str(item.get("asset") or ""),
            "thesis": str(item.get("summary") or ""),
            "confidence": float(item.get("confidence") or 0.0),
            "status": str(item.get("status") or "pending"),
        }
        for item in recommendations[:6]
    ]
    st.dataframe(
        signal_rows,
        use_container_width=True,
        hide_index=True,
    )

with col_activity:
    st.markdown("### Recent Activity")
    for line in recent_activity[:6]:
        st.markdown(f"- {line}")
