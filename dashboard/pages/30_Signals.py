from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.asset_detail import (
    render_asset_detail_card,
    render_evidence_section,
    render_research_lens,
)
from dashboard.components.cards import render_kpi_cards
from dashboard.components.focus_selector import render_focus_selector
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_signals_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_signals_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

signals_view = get_signals_view()
signals = signals_view.get("signals") if isinstance(signals_view.get("signals"), list) else []
selected_asset, default_asset, _asset_options = render_focus_selector(
    signals,
    label="Focus signal",
    selected_asset=str(signals_view.get("selected_asset") or ""),
    fallback_asset="SOL",
    key="signals_selected_asset",
)
if selected_asset != default_asset:
    signals_view = get_signals_view(selected_asset=selected_asset)
    signals = signals_view.get("signals") if isinstance(signals_view.get("signals"), list) else signals

detail = signals_view.get("detail") if isinstance(signals_view.get("detail"), dict) else {}

render_page_header(
    "Signals",
    "AI recommendations with the same research/evidence detail model used by Markets.",
    badges=[
        {"label": "Asset", "value": str(detail.get("asset") or default_asset)},
        {"label": "Status", "value": str(detail.get("status") or "monitor").replace("_", " ").title()},
    ],
)

render_kpi_cards(build_signals_kpis(detail))

left, right = st.columns((1, 1.4))

with left:
    render_table_section(
        "Signal Queue",
        [
            {
                "asset": str(item.get("asset") or ""),
                "signal": str(item.get("signal") or ""),
                "confidence": float(item.get("confidence") or 0.0),
                "status": str(item.get("status") or ""),
                "price": float(item.get("price") or 0.0),
                "change_24h_pct": float(item.get("change_24h_pct") or 0.0),
            }
            for item in signals
            if isinstance(item, dict)
        ],
        empty_message="No recommendation data available.",
    )
    with st.container(border=True):
        st.markdown("### Signal Thesis")
        selected_row = next(
            (item for item in signals if isinstance(item, dict) and str(item.get("asset") or "") == str(detail.get("asset") or default_asset)),
            {},
        )
        st.caption(str(selected_row.get("summary") or detail.get("current_cause") or "No signal thesis available."))
        st.caption(f"Evidence: {str(selected_row.get('evidence') or detail.get('evidence') or 'No evidence available.')}")

with right:
    render_asset_detail_card(
        detail,
        title="Signal Detail",
        fallback_asset=default_asset,
        empty_message="No signal detail available.",
        footer=(
            f"Market bias: {str(detail.get('market_bias') or 'balanced').replace('_', ' ').title()}. "
            f"Volume trend: {str(detail.get('volume_trend') or 'steady').title()}."
        ),
    )

bottom_left, bottom_right = st.columns((1, 1))

with bottom_left:
    render_evidence_section(detail)

with bottom_right:
    render_research_lens(detail, question_fallback="Why is this signal active?")
