from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_kpi_cards
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_signals_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

signals_view = get_signals_view()
signals = signals_view.get("signals") if isinstance(signals_view.get("signals"), list) else []
asset_options = [str(item.get("asset") or "") for item in signals if isinstance(item, dict)]
default_asset = str(signals_view.get("selected_asset") or (asset_options[0] if asset_options else "SOL"))
selected_asset = st.selectbox(
    "Focus signal",
    asset_options or [default_asset],
    index=(asset_options.index(default_asset) if default_asset in asset_options else 0),
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

render_kpi_cards(
    [
        {
            "label": "Signal",
            "value": str(detail.get("signal") or "watch").replace("_", " ").title(),
            "delta": str(detail.get("status") or "monitor").replace("_", " ").title(),
        },
        {
            "label": "Confidence",
            "value": f"{float(detail.get('confidence') or 0.0) * 100:.0f}%",
            "delta": "AI conviction",
        },
        {
            "label": "24h Change",
            "value": f"{float(detail.get('change_24h_pct') or 0.0):+.1f}%",
            "delta": f"${float(detail.get('price') or 0.0):,.2f}",
        },
        {
            "label": "Execution",
            "value": "Disabled" if bool(detail.get("execution_disabled", True)) else "Enabled",
            "delta": str(detail.get("risk_note") or "Policy managed"),
        },
    ]
)

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
    st.markdown("### Signal Detail")
    with st.container(border=True):
        st.markdown(f"#### {str(detail.get('asset') or default_asset)}")
        st.caption(str(detail.get("current_cause") or detail.get("thesis") or "No signal detail available."))
        st.line_chart(detail.get("price_series") or [], use_container_width=True)
        st.caption(
            f"Market bias: {str(detail.get('market_bias') or 'balanced').replace('_', ' ').title()}. "
            f"Volume trend: {str(detail.get('volume_trend') or 'steady').title()}."
        )

bottom_left, bottom_right = st.columns((1, 1))

with bottom_left:
    render_table_section(
        "Evidence",
        detail.get("evidence_items") if isinstance(detail.get("evidence_items"), list) else [],
        empty_message="No supporting evidence available.",
    )

with bottom_right:
    with st.container(border=True):
        st.markdown("### Research Lens")
        st.caption(str(detail.get("question") or "Why is this signal active?"))
        st.markdown(f"**Current Cause**  \n{str(detail.get('current_cause') or 'No current-cause summary available.')}")
        st.markdown(f"**Past Precedent**  \n{str(detail.get('past_precedent') or 'No historical precedent available.')}")
        st.markdown(f"**Future Catalyst**  \n{str(detail.get('future_catalyst') or 'No forward catalyst available.')}")
