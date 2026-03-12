from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_feature_hero, render_kpi_cards, render_prompt_actions
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_trades_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_trade_failure_summary, render_trades_queue_summary
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

lead_approval = pending_approvals[0] if pending_approvals else {}
hero_title = (
    f"{len(pending_approvals)} approval{'s' if len(pending_approvals) != 1 else ''} waiting"
    if approval_required
    else "Execution flow is clear"
)
hero_summary = (
    f"{str(lead_approval.get('asset') or 'No asset')} is waiting for manual review before execution can continue."
    if pending_approvals
    else "No approvals are waiting. Recent fills and order state are below."
)

render_feature_hero(
    eyebrow="Execution Workspace",
    title=hero_title,
    summary=hero_summary,
    body="Pending approvals stay primary. Open orders, failures, and fills are secondary execution context.",
    badges=[
        {
            "text": "Approval Required" if approval_required else "Auto Approved",
            "tone": "danger" if approval_required else "success",
        },
        {"text": f"{len(open_orders)} Open Orders", "tone": "muted"},
        {"text": f"{len(failed_orders)} Failures", "tone": "warning"},
    ],
    metrics=[
        {"label": "Pending", "value": str(len(pending_approvals)), "delta": str(lead_approval.get("asset") or "Queue clear")},
        {"label": "Open Orders", "value": str(len(open_orders)), "delta": "Live order state"},
        {"label": "Recent Fills", "value": str(len(recent_fills)), "delta": "Execution history"},
        {"label": "Failures", "value": str(len(failed_orders)), "delta": "Rejected / canceled"},
    ],
    aside_title="Ask Copilot",
    aside_lines=[
        "Explain why this approval is required",
        "Summarize execution failures",
        "What changed in recent fills?",
    ],
)

render_prompt_actions(
    title="Copilot Shortcuts",
    prompts=[
        "Explain why this approval is required",
        "Summarize recent fills",
        "Summarize failures",
    ],
    key_prefix="trades",
)

summary_col, table_col = st.columns((0.95, 1.05))

with summary_col:
    render_trades_queue_summary(pending_approvals, open_orders, failed_orders, recent_fills)
    render_trade_failure_summary(failed_orders)

with table_col:
    render_table_section(
        "Pending Approvals",
        pending_approvals,
        subtitle="Queue needing explicit review before execution can proceed.",
        empty_message="No pending approvals.",
    )
    render_table_section(
        "Open Orders",
        open_orders,
        subtitle="Orders currently working in the paper or simulated execution layer.",
        empty_message="No open orders.",
    )
    render_table_section(
        "Failed / Canceled",
        failed_orders,
        subtitle="Rejected or canceled orders that need follow-up or explanation.",
        empty_message="No failed or canceled orders.",
    )

render_table_section(
    "Recent Fills",
    recent_fills,
    subtitle="Most recent execution outcomes across the active workflow.",
    empty_message="No recent fills.",
)
