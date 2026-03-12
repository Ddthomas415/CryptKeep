from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_kpi_cards
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_trades_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_trades_queue_summary
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_trades_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()
trades_view = get_trades_view()
pending_approvals = (
    trades_view.get("pending_approvals") if isinstance(trades_view.get("pending_approvals"), list) else []
)
open_orders = trades_view.get("open_orders") if isinstance(trades_view.get("open_orders"), list) else []
failed_orders = trades_view.get("failed_orders") if isinstance(trades_view.get("failed_orders"), list) else []
recent_fills = trades_view.get("recent_fills") if isinstance(trades_view.get("recent_fills"), list) else []
approval_required = bool(trades_view.get("approval_required", True))

render_page_header(
    "Trades",
    "Approvals, orders, and fills with execution state clarity.",
    badges=[{"label": "Safety", "value": "Approval Required" if approval_required else "Auto Approved"}],
)

render_kpi_cards(
    build_trades_kpis(
        approval_required=approval_required,
        pending_approvals=pending_approvals,
        open_orders=open_orders,
        failed_orders=failed_orders,
        recent_fills=recent_fills,
    )
)

summary_col, table_col = st.columns((1, 1.4))

with summary_col:
    render_trades_queue_summary(pending_approvals, open_orders, failed_orders, recent_fills)

with table_col:
    render_table_section(
        "Pending Approvals",
        pending_approvals,
        empty_message="No pending approvals.",
    )
    render_table_section(
        "Open Orders",
        open_orders,
        empty_message="No open orders.",
    )
    render_table_section(
        "Failed / Canceled",
        failed_orders,
        empty_message="No failed or canceled orders.",
    )

render_table_section(
    "Recent Fills",
    recent_fills,
    empty_message="No recent fills.",
)
