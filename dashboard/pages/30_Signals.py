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
from dashboard.components.kpi_builders import build_signals_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import render_signal_thesis
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

selected_asset_name = str(detail.get("asset") or default_asset)
selected_signal = str(detail.get("signal") or "watch").replace("_", " ").title()
selected_status = str(detail.get("status") or "monitor").replace("_", " ").title()
selected_category = str(detail.get("category") or "needs_confirmation").replace("_", " ").title()
execution_label = str(detail.get("execution_state") or "disabled").replace("_", " ").title()

render_feature_hero(
    eyebrow="AI Recommendation View",
    title=f"{selected_asset_name} · {selected_signal}",
    summary=str(detail.get("current_cause") or "No selected-signal thesis available."),
    body=str(detail.get("future_catalyst") or detail.get("risk_note") or ""),
    badges=[
        {"text": selected_status, "tone": "accent"},
        {"text": selected_category, "tone": "warning"},
        {"text": execution_label, "tone": "muted"},
    ],
    metrics=[
        {
            "label": "Confidence",
            "value": f"{float(detail.get('confidence') or 0.0) * 100:.0f}%",
            "delta": "AI conviction",
        },
        {
            "label": "Opportunity",
            "value": selected_category,
            "delta": f"Score {float(detail.get('opportunity_score') or 0.0) * 100:.0f}%",
        },
        {
            "label": "24h Change",
            "value": f"{float(detail.get('change_24h_pct') or 0.0):+.1f}%",
            "delta": f"${float(detail.get('price') or 0.0):,.2f}" if float(detail.get("price") or 0.0) else "-",
        },
        {
            "label": "Execution",
            "value": execution_label,
            "delta": "Research only" if bool(detail.get("execution_disabled", True)) else "Execution enabled",
        },
    ],
    aside_title="Ask Copilot",
    aside_lines=[
        f"Ask Copilot about {selected_asset_name}",
        "Why does this signal exist?",
        "What are the risks?",
        "What changed since the last signal?",
    ],
)

render_prompt_actions(
    title="Copilot Shortcuts",
    prompts=[
        f"Ask Copilot about {selected_asset_name}",
        "Why is this signal active?",
        "Summarize the evidence",
    ],
    key_prefix="signals",
)

left, right = st.columns((0.92, 1.08))

with left:
    render_table_section(
        "Signal Queue",
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
                "price": float(item.get("price") or 0.0),
                "change_24h_pct": float(item.get("change_24h_pct") or 0.0),
            }
            for item in signals
            if isinstance(item, dict)
        ],
        subtitle="Review recommendation state, runtime execution context, and opportunity score before acting.",
        empty_message="No recommendation data available.",
    )
    render_signal_thesis(signals, detail, fallback_asset=default_asset)

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
    render_research_lens(detail, title="AI Research Lens", question_fallback="Why is this signal active?")
