from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.asset_detail import (
    render_asset_detail_card,
    render_evidence_section,
    render_research_lens,
)
from dashboard.components.cards import render_kpi_cards
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_markets_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

markets_view = get_markets_view()
watchlist = markets_view.get("watchlist") if isinstance(markets_view.get("watchlist"), list) else []
asset_options = [str(item.get("asset") or "") for item in watchlist if isinstance(item, dict)]
default_asset = str(markets_view.get("selected_asset") or (asset_options[0] if asset_options else "BTC"))
selected_asset = st.selectbox(
    "Focus asset",
    asset_options or [default_asset],
    index=(asset_options.index(default_asset) if default_asset in asset_options else 0),
    key="markets_selected_asset",
)
if selected_asset != default_asset:
    markets_view = get_markets_view(selected_asset=selected_asset)
    watchlist = markets_view.get("watchlist") if isinstance(markets_view.get("watchlist"), list) else watchlist

detail = markets_view.get("detail") if isinstance(markets_view.get("detail"), dict) else {}
market_bias = str(detail.get("market_bias") or "balanced").replace("_", " ").title()

render_page_header(
    "Markets",
    "Watchlist-first market intelligence view with selected-asset context and signal alignment.",
    badges=[
        {"label": "Asset", "value": str(detail.get("asset") or default_asset)},
        {"label": "Bias", "value": market_bias},
    ],
)

render_kpi_cards(
    [
        {
            "label": "Last Price",
            "value": f"${float(detail.get('price') or 0.0):,.2f}",
            "delta": f"24h {float(detail.get('change_24h_pct') or 0.0):+.1f}%",
        },
        {
            "label": "Signal State",
            "value": str(detail.get("signal") or "watch").replace("_", " ").title(),
            "delta": str(detail.get("status") or "monitor").replace("_", " ").title(),
        },
        {
            "label": "Confidence",
            "value": f"{float(detail.get('confidence') or 0.0) * 100:.0f}%",
            "delta": "AI conviction",
        },
        {
            "label": "Volume Trend",
            "value": str(detail.get("volume_trend") or "steady").title(),
            "delta": "Watchlist context",
        },
    ]
)

left, right = st.columns((1, 1.4))

with left:
    render_table_section(
        "Watchlist",
        [
            {
                "asset": str(item.get("asset") or ""),
                "price": float(item.get("price") or 0.0),
                "change_24h_pct": float(item.get("change_24h_pct") or 0.0),
                "signal": str(item.get("signal") or ""),
                "confidence": float(item.get("confidence") or 0.0),
            }
            for item in watchlist
            if isinstance(item, dict)
        ],
        empty_message="No watchlist data available.",
    )
    with st.container(border=True):
        st.markdown("### Market Context")
        st.caption(f"Support: ${float(detail.get('support') or 0.0):,.2f}")
        st.caption(f"Resistance: ${float(detail.get('resistance') or 0.0):,.2f}")
        st.caption(f"Evidence: {str(detail.get('evidence') or 'No evidence available.')}")

with right:
    render_asset_detail_card(
        detail,
        title="Asset Detail",
        fallback_asset=default_asset,
        empty_message="No asset thesis available.",
        footer=(
            f"Market bias: {market_bias}. Workflow status: "
            f"{str(detail.get('status') or 'monitor').replace('_', ' ')}."
        ),
    )

bottom_left, bottom_right = st.columns((1, 1))

with bottom_left:
    render_table_section(
        "Related Signals",
        detail.get("related_signals") if isinstance(detail.get("related_signals"), list) else [],
        empty_message="No related signals available.",
    )

with bottom_right:
    render_evidence_section(detail)

render_research_lens(detail)
