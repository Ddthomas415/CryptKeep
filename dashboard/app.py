

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) in sys.path:
    sys.path.remove(str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.styles.theme_enhanced import inject_enhanced_theme, inject_signin_button
from dashboard.components.activity import render_activity_panel
from dashboard.components.asset_detail import build_assistant_status_summary
from dashboard.components.cards import render_feature_hero, render_kpi_cards, render_prompt_actions
from dashboard.components.focus_selector import render_focus_selector
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import build_overview_kpis
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import (
    render_collector_runtime_summary,
    render_home_digest_summary,
    render_overview_status_summary,
    render_structural_edge_digest_summary,
    render_structural_edge_health_summary,
    render_structural_edge_summary,
)
from dashboard.components.tables import render_table_section
from dashboard.services.crypto_edge_research import (
    load_crypto_edge_collector_runtime,
    load_crypto_edge_staleness_digest,
    load_crypto_edge_staleness_summary,
    load_latest_live_crypto_edge_snapshot,
)
from dashboard.services.digest.builders import load_home_digest
from dashboard.services.view_data import get_overview_view

st.set_page_config(page_title="CryptKeep", layout="wide", page_icon=":chart_with_upwards_trend:")

inject_enhanced_theme()
inject_signin_button()

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

overview_view = get_overview_view()
signal_rows = overview_view.get("signals") if isinstance(overview_view.get("signals"), list) else []
detail = overview_view.get("detail") if isinstance(overview_view.get("detail"), dict) else {}
focus_asset, default_asset, _focus_options = render_focus_selector(
    signal_rows,
    label="Focus signal",
    selected_asset=str(overview_view.get("selected_asset") or ""),
    fallback_asset="SOL",
    key="overview_selected_signal",
)
if focus_asset != default_asset:
    overview_view = get_overview_view(selected_asset=focus_asset)
    signal_rows = overview_view.get("signals") if isinstance(overview_view.get("signals"), list) else signal_rows
    detail = overview_view.get("detail") if isinstance(overview_view.get("detail"), dict) else detail

summary = overview_view.get("summary") if isinstance(overview_view.get("summary"), dict) else {}
portfolio = summary.get("portfolio") if isinstance(summary.get("portfolio"), dict) else {}
recent_activity = overview_view.get("recent_activity") if isinstance(overview_view.get("recent_activity"), list) else []
watchlist_preview = (
    overview_view.get("watchlist_preview") if isinstance(overview_view.get("watchlist_preview"), list) else []
)
live_structural_edges = load_latest_live_crypto_edge_snapshot()
collector_runtime = load_crypto_edge_collector_runtime()
structural_edge_health = load_crypto_edge_staleness_summary()
structural_edge_digest = load_crypto_edge_staleness_digest()
home_digest = load_home_digest(summary)

mode = str(summary.get("mode") or "research_only")
risk_status = str(summary.get("risk_status") or "safe")
execution_enabled = bool(summary.get("execution_enabled", False))

render_page_header(
    "Overview",
    "Primary workspace for opportunity review, risk posture, and AI-guided market focus.",
    badges=[
        {"label": "Mode", "value": mode.replace("_", " ").title()},
    ],
)

render_kpi_cards(build_overview_kpis(portfolio=portfolio, signal_count=len(signal_rows), execution_enabled=execution_enabled))
render_home_digest_summary(home_digest)

assistant_summary = build_assistant_status_summary(detail)
hero_badges = [
    {"text": str(detail.get("category") or "needs_confirmation").replace("_", " ").title(), "tone": "accent"},
    {"text": str(detail.get("regime") or "unknown").replace("_", " ").title(), "tone": "muted"},
]
if str(detail.get("execution_state") or "").strip():
    hero_badges.append({"text": str(detail.get("execution_state") or "").replace("_", " ").title(), "tone": "warning"})
elif bool(detail.get("execution_disabled", True)):
    hero_badges.append({"text": "Research Only", "tone": "success"})

hero_metrics = [
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
        "label": "Opportunity",
        "value": f"{float(detail.get('opportunity_score') or 0.0) * 100:.0f}%",
        "delta": str(detail.get("category") or "needs_confirmation").replace("_", " ").title(),
    },
    {
        "label": "24h Move",
        "value": f"{float(detail.get('change_24h_pct') or 0.0):+.1f}%",
        "delta": f"${float(detail.get('price') or 0.0):,.2f}" if float(detail.get("price") or 0.0) else "-",
    },
]

hero_col, side_col = st.columns((1.45, 0.95))

with hero_col:
    render_feature_hero(
        eyebrow="Top Opportunity",
        title=f"{str(detail.get('asset') or default_asset)} · {str(detail.get('signal') or 'watch').replace('_', ' ').title()}",
        summary=str(detail.get("current_cause") or "No focused signal detail available."),
        body=str(detail.get("future_catalyst") or detail.get("risk_note") or ""),
        badges=hero_badges,
        metrics=hero_metrics,
        aside_title="AI Copilot",
        aside_lines=[
            assistant_summary,
            f"Status: {str(detail.get('status') or 'monitor').replace('_', ' ').title()}",
            f"Execution: {str(detail.get('execution_state') or 'disabled').replace('_', ' ').title()}",
            str(detail.get("risk_note") or "Execution remains disabled until policies allow it."),
        ],
    )
    render_prompt_actions(
        title="Ask Copilot",
        prompts=[
            "What changed while I was away?",
            "Explain this focused signal",
            "Summarize workspace risk",
        ],
        key_prefix="overview_copilot",
    )

with side_col:
    render_overview_status_summary(summary)
    render_structural_edge_digest_summary(
        structural_edge_digest,
        title="While-Away Structural Digest",
        subtitle="Compact stale-data and change summary for live-public structural-edge research.",
    )
    render_structural_edge_health_summary(
        structural_edge_health,
        title="Structural Edge Freshness",
        subtitle="Live-public structural-edge freshness and collector loop health.",
    )
    render_collector_runtime_summary(
        collector_runtime,
        title="Collector Loop",
        subtitle="Read-only collector loop status for live-public structural-edge snapshots.",
    )
    render_structural_edge_summary(
        live_structural_edges,
        title="Live Structural Snapshot",
        subtitle="Latest live-public funding, basis, and dislocation context kept separate from sample research data.",
    )
    render_table_section(
        "Watchlist Snapshot",
        watchlist_preview,
        empty_message="No watchlist data available.",
    )

col_signals, col_activity = st.columns((1.3, 1))

with col_signals:
    render_table_section(
        "Recent Signals",
        signal_rows,
        empty_message="No recent signals available.",
    )

with col_activity:
    render_activity_panel(recent_activity)
