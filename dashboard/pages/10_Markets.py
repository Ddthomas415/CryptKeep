from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.asset_detail import (
    render_asset_detail_card,
    render_evidence_section,
    render_research_lens,
)
from dashboard.components.cards import render_feature_hero, render_kpi_cards, render_prompt_actions
from dashboard.components.focus_selector import render_focus_selector
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_markets_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_market_context
from dashboard.components.tables import render_table_section
from dashboard.services.view_data import get_markets_view

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

markets_view = get_markets_view()
watchlist = markets_view.get("watchlist") if isinstance(markets_view.get("watchlist"), list) else []
selected_asset, default_asset, _asset_options = render_focus_selector(
    watchlist,
    label="Focus asset",
    selected_asset=str(markets_view.get("selected_asset") or ""),
    fallback_asset="BTC",
    key="markets_selected_asset",
)
if selected_asset != default_asset:
    markets_view = get_markets_view(selected_asset=selected_asset)
    watchlist = markets_view.get("watchlist") if isinstance(markets_view.get("watchlist"), list) else watchlist

detail = markets_view.get("detail") if isinstance(markets_view.get("detail"), dict) else {}
market_bias = str(detail.get("market_bias") or "balanced").replace("_", " ").title()
selected_asset_name = str(detail.get("asset") or default_asset)
selected_signal = str(detail.get("signal") or "watch").replace("_", " ").title()
selected_status = str(detail.get("status") or "monitor").replace("_", " ").title()
selected_category = str(detail.get("category") or "needs_confirmation").replace("_", " ").title()

render_page_header(
    "Markets",
    "Watchlist-first market intelligence view with selected-asset context and signal alignment.",
    badges=[
        {"label": "Asset", "value": str(detail.get("asset") or default_asset)},
        {"label": "Bias", "value": market_bias},
    ],
)

render_kpi_cards(build_markets_kpis(detail))

render_feature_hero(
    eyebrow="Flagship Market View",
    title=f"{selected_asset_name} · {market_bias}",
    summary=str(detail.get("current_cause") or "No selected-asset summary available."),
    body=str(detail.get("future_catalyst") or detail.get("risk_note") or ""),
    badges=[
        {"text": selected_signal, "tone": "accent"},
        {"text": selected_status, "tone": "muted"},
        {"text": selected_category, "tone": "warning"},
    ],
    metrics=[
        {
            "label": "Last Price",
            "value": f"${float(detail.get('price') or 0.0):,.2f}",
            "delta": f"24h {float(detail.get('change_24h_pct') or 0.0):+.1f}%",
        },
        {
            "label": "Signal State",
            "value": selected_signal,
            "delta": selected_status,
        },
        {
            "label": "Confidence",
            "value": f"{float(detail.get('confidence') or 0.0) * 100:.0f}%",
            "delta": "AI conviction",
        },
        {
            "label": "Opportunity",
            "value": selected_category,
            "delta": (
                f"Score {float(detail.get('opportunity_score') or 0.0) * 100:.0f}% / "
                f"{str(detail.get('regime') or 'unknown').replace('_', ' ').title()}"
            ),
        },
    ],
    aside_title="Ask Copilot",
    aside_lines=[
        f"Ask Copilot about {selected_asset_name}",
        "Why is this moving right now?",
        "What changed in the last hour?",
        "What invalidates this setup?",
    ],
)

render_prompt_actions(
    title="Copilot Shortcuts",
    prompts=[
        f"Ask Copilot about {selected_asset_name}",
        f"Why is {selected_asset_name} moving?",
        f"What are the risks for {selected_asset_name}?",
    ],
    key_prefix="markets",
)

render_asset_detail_card(
    detail,
    title="Selected Asset",
    fallback_asset=default_asset,
    empty_message="No asset thesis available.",
    footer=(
        f"Market bias: {market_bias}. Workflow status: "
        f"{str(detail.get('status') or 'monitor').replace('_', ' ')}."
    ),
)

left, right = st.columns((0.95, 1.05))

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
                "regime": str(item.get("regime") or ""),
                "category": str(item.get("category") or ""),
                "opportunity_score": float(item.get("opportunity_score") or 0.0),
            }
            for item in watchlist
            if isinstance(item, dict)
        ],
        subtitle="Monitor market state, confidence, regime, and opportunity score across the active watchlist.",
        empty_message="No watchlist data available.",
    )
    render_market_context(detail)

with right:
    render_table_section(
        "Related Signals",
        [
            {
                "asset": str(item.get("asset") or ""),
                "signal": str(item.get("signal") or ""),
                "confidence": float(item.get("confidence") or 0.0),
                "status": str(item.get("status") or ""),
                "execution_state": str(item.get("execution_state") or ""),
                "regime": str(item.get("regime") or ""),
                "category": str(item.get("category") or ""),
                "opportunity_score": float(item.get("opportunity_score") or 0.0),
                "summary": str(item.get("summary") or ""),
            }
            for item in (
                detail.get("related_signals") if isinstance(detail.get("related_signals"), list) else []
            )
            if isinstance(item, dict)
        ],
        subtitle="Connected recommendations aligned to the same asset context and current market regime.",
        empty_message="No related signals available.",
    )
    render_evidence_section(detail)

render_research_lens(detail, title="AI Research Lens")
