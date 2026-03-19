from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.digest import (
    render_attention_now,
    render_crypto_edge_summary,
    render_digest_page_header,
    render_freshness_panel,
    render_leaderboard_summary,
    render_mode_truth_card,
    render_next_best_action,
    render_recent_incidents,
    render_runtime_truth_strip,
    render_safety_warnings,
    render_scorecard_snapshot,
)
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.services.digest.builders import build_home_digest

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

render_page_header(
    "Home Digest",
    "Current operating truth for strategy, safety, and research freshness.",
)

try:
    digest = build_home_digest()
except Exception as exc:
    st.error("Home Digest unavailable")
    st.caption(f"Reason: {type(exc).__name__}")
    st.caption("Next: review upstream summary builders and collector/runtime availability.")
else:
    render_digest_page_header(digest)
    render_runtime_truth_strip(digest["runtime_truth"])

    col_main, col_side = st.columns([1.5, 1])

    with col_main:
        render_attention_now(digest["attention_now"])
        render_leaderboard_summary(digest["leaderboard_summary"])
        render_scorecard_snapshot(digest["scorecard_snapshot"])

    with col_side:
        render_crypto_edge_summary(digest["crypto_edge_summary"])
        render_safety_warnings(digest["safety_warnings"])
        render_mode_truth_card(digest["mode_truth"])

    render_freshness_panel(digest["freshness_panel"])
    render_recent_incidents(digest["recent_incidents"])
    render_next_best_action(digest["next_best_action"])
