from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_feature_hero, render_kpi_cards, render_prompt_actions
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.tables import render_table_section
from dashboard.services.crypto_edge_research import (
    load_crypto_edge_collector_runtime,
    load_crypto_edge_staleness_digest,
    load_crypto_edge_workspace,
    load_latest_live_crypto_edge_snapshot,
)

SOURCE_FILTER_OPTIONS = ["All Sources", "Live Public", "Sample Bundle", "Manual Import"]
FRESHNESS_FILTER_OPTIONS = ["All Freshness", "Fresh", "Recent", "Aging", "Stale", "Unknown"]


def _matches_filter(row: dict[str, object], *, source_filter: str, freshness_filter: str) -> bool:
    source_ok = source_filter == "All Sources" or str(row.get("source_label") or row.get("source") or "") == source_filter
    freshness_ok = freshness_filter == "All Freshness" or str(row.get("freshness") or "") == freshness_filter
    return source_ok and freshness_ok


AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

workspace = load_crypto_edge_workspace()
live_snapshot = load_latest_live_crypto_edge_snapshot()
collector_runtime = load_crypto_edge_collector_runtime()
staleness_digest = load_crypto_edge_staleness_digest()
render_page_header(
    "Research",
    "Crypto-native structural edge workspace for funding, basis, and cross-venue dislocation analysis.",
    badges=[
        {"label": "Mode", "value": "Research Only"},
        {
            "label": "Data",
            "value": str(workspace.get("data_origin_label") or "Stored Snapshots")
            if bool(workspace.get("has_any_data"))
            else "No Snapshots",
        },
        {
            "label": "Freshness",
            "value": str(workspace.get("freshness_summary") or "Unknown")
            if bool(workspace.get("has_any_data"))
            else "N/A",
        },
    ],
)

render_feature_hero(
    eyebrow="Structural Edge Workspace",
    title="Funding Carry, Basis, and Cross-Venue Dislocations",
    summary=(
        "Use stored snapshots to review crypto-native market structure without coupling this research to execution."
    ),
    body=(
        "Load bundled sample data with `make load-sample-crypto-edges`, collect public live snapshots with "
        "`make collect-live-crypto-edges`, or ingest your own JSON snapshots with "
        "`scripts/record_crypto_edge_snapshot.py`."
    ),
    badges=[
        {"text": "Read Only", "tone": "warning"},
        {"text": "Execution Disabled", "tone": "danger"},
        {"text": "Snapshot Store", "tone": "muted"},
    ],
    metrics=[
        {
            "label": "Funding Rows",
            "value": str(int(((workspace.get("funding") or {}).get("count") or 0))),
            "delta": str(((workspace.get("funding_meta") or {}).get("capture_ts") or "No snapshot")),
        },
        {
            "label": "Basis Rows",
            "value": str(int(((workspace.get("basis") or {}).get("count") or 0))),
            "delta": str(((workspace.get("basis_meta") or {}).get("capture_ts") or "No snapshot")),
        },
        {
            "label": "Quote Rows",
            "value": str(int(((workspace.get("dislocations") or {}).get("count") or 0))),
            "delta": str(((workspace.get("quote_meta") or {}).get("capture_ts") or "No snapshot")),
        },
        {
            "label": "Origin",
            "value": str(workspace.get("data_origin_label") or ("Ready" if bool(workspace.get("has_any_data")) else "Empty")),
            "delta": str(workspace.get("freshness_summary") or "Unknown"),
        },
    ],
    aside_title="Ask Copilot",
    aside_lines=[
        "Summarize funding carry state",
        "Explain current basis structure",
        "Show top cross-venue dislocations",
        "Summarize latest live structural edge snapshot",
        "Summarize stale-data risk",
        "What changed while I was away?",
    ],
)

render_prompt_actions(
    title="Copilot Shortcuts",
    prompts=[
        "Summarize funding carry state",
        "Explain current basis structure",
        "Show top cross-venue dislocations",
        "Summarize latest live structural edge snapshot",
        "Summarize stale-data risk",
        "What changed while I was away?",
    ],
    key_prefix="research",
)

render_table_section(
    "Stale-Data Digest",
    [
        {
            "headline": str(staleness_digest.get("headline") or "Structural-edge data status"),
            "severity": str(staleness_digest.get("severity") or "ok"),
            "attention": "yes" if bool(staleness_digest.get("needs_attention")) else "no",
            "summary": str(staleness_digest.get("while_away_summary") or staleness_digest.get("summary_text") or ""),
        }
    ]
    if bool(staleness_digest.get("ok"))
    else [],
    subtitle="Compact stale-data and while-away digest built from live snapshot freshness, collector runtime, and stored change summaries.",
    empty_message="No stale-data digest is available yet.",
)

render_table_section(
    "Collector Runtime",
    [
        {
            "status": str(collector_runtime.get("status") or "not_started"),
            "source": str(collector_runtime.get("source_label") or collector_runtime.get("source") or "Live Public"),
            "freshness": str(collector_runtime.get("freshness") or "Unknown"),
            "loops": int(collector_runtime.get("loops") or 0),
            "writes": int(collector_runtime.get("writes") or 0),
            "errors": int(collector_runtime.get("errors") or 0),
            "last_reason": str(collector_runtime.get("last_reason") or collector_runtime.get("reason") or ""),
            "summary": str(collector_runtime.get("summary_text") or ""),
        }
    ]
    if bool(collector_runtime.get("has_status"))
    else [],
    subtitle="Latest runtime health from the read-only live structural-edge collector loop.",
    empty_message="Collector loop has not reported status yet. Use `make collect-live-crypto-edges-loop` to start it.",
)

filter_left, filter_right = st.columns((1, 1))
with filter_left:
    source_filter = st.selectbox(
        "Snapshot Source",
        SOURCE_FILTER_OPTIONS,
        index=0,
        key="research_source_filter",
    )
with filter_right:
    freshness_filter = st.selectbox(
        "Freshness Filter",
        FRESHNESS_FILTER_OPTIONS,
        index=0,
        key="research_freshness_filter",
    )

if not bool(workspace.get("ok")):
    st.warning(f"Crypto research workspace unavailable: {str(workspace.get('reason') or 'unknown_error')}")
elif not bool(workspace.get("has_any_data")):
    st.info(
        "No stored crypto-edge snapshots yet. Run `make load-sample-crypto-edges` for bundled demo data or "
        "`scripts/record_crypto_edge_snapshot.py` for your own research-only snapshots."
    )
else:
    funding = dict(workspace.get("funding") or {})
    basis = dict(workspace.get("basis") or {})
    dislocations = dict(workspace.get("dislocations") or {})
    funding_history = [
        row
        for row in list(workspace.get("funding_history") or [])
        if _matches_filter(dict(row or {}), source_filter=source_filter, freshness_filter=freshness_filter)
    ]
    basis_history = [
        row
        for row in list(workspace.get("basis_history") or [])
        if _matches_filter(dict(row or {}), source_filter=source_filter, freshness_filter=freshness_filter)
    ]
    dislocation_history = [
        row
        for row in list(workspace.get("dislocation_history") or [])
        if _matches_filter(dict(row or {}), source_filter=source_filter, freshness_filter=freshness_filter)
    ]
    provenance_rows = [
        row
        for row in list(workspace.get("provenance_rows") or [])
        if _matches_filter(dict(row or {}), source_filter=source_filter, freshness_filter=freshness_filter)
    ]
    history_rows = [
        row
        for row in list(workspace.get("history_rows") or [])
        if _matches_filter(dict(row or {}), source_filter=source_filter, freshness_filter=freshness_filter)
    ]
    live_snapshot_visible = bool(live_snapshot.get("has_live_data")) and source_filter in {"All Sources", "Live Public"}
    if live_snapshot_visible and freshness_filter != "All Freshness":
        live_snapshot_visible = str(live_snapshot.get("freshness_summary") or "") == freshness_filter

    render_kpi_cards(
        [
            {
                "label": "Funding Carry",
                "value": f"{float(funding.get('annualized_carry_pct') or 0.0):.2f}%",
                "delta": str(funding.get("dominant_bias") or "flat").replace("_", " ").title(),
            },
            {
                "label": "Average Basis",
                "value": f"{float(basis.get('avg_basis_bps') or 0.0):.2f} bps",
                "delta": f"Widest {float(basis.get('widest_basis_bps') or 0.0):.2f} bps",
            },
            {
                "label": "Positive Dislocations",
                "value": str(int(dislocations.get("positive_count") or 0)),
                "delta": "Cross-venue positive gaps",
            },
            {
                "label": "Top Symbol",
                "value": str(((dislocations.get("top_dislocation") or {}).get("symbol") or "-")),
                "delta": (
                    f"{float(((dislocations.get('top_dislocation') or {}).get('gross_cross_bps') or 0.0)):.2f} bps"
                    if dislocations.get("top_dislocation")
                    else "No positive dislocation"
                ),
            },
        ]
    )

    render_table_section(
        "What Changed",
        list(workspace.get("trend_rows") or [])
        if source_filter == "All Sources" and freshness_filter == "All Freshness"
        else [],
        subtitle=(
            "Latest snapshot deltas versus the prior stored snapshot for each structural research theme."
            if source_filter == "All Sources" and freshness_filter == "All Freshness"
            else "Global trend deltas are shown only for the unfiltered all-sources view."
        ),
        empty_message="Not enough history yet to compare snapshots.",
    )
    render_table_section(
        "Snapshot Provenance",
        provenance_rows,
        subtitle="Current source and freshness for the latest stored snapshot in each research stream.",
        empty_message="No snapshot provenance available.",
    )
    render_table_section(
        "Latest Live Structural Snapshot",
        [
            {
                "source": str(live_snapshot.get("data_origin_label") or "Live Public"),
                "freshness": str(live_snapshot.get("freshness_summary") or "Unknown"),
                "funding_bias": str(((live_snapshot.get("funding") or {}).get("dominant_bias") or "flat")),
                "avg_basis_bps": f"{float(((live_snapshot.get('basis') or {}).get('avg_basis_bps') or 0.0)):.2f}",
                "positive_dislocations": int(((live_snapshot.get("dislocations") or {}).get("positive_count") or 0)),
                "top_symbol": str((((live_snapshot.get("dislocations") or {}).get("top_dislocation") or {}).get("symbol") or "-")),
                "summary": str(live_snapshot.get("summary_text") or ""),
            }
        ]
        if live_snapshot_visible
        else [],
        subtitle="Latest stored live-public structural edge snapshot isolated from sample or manual research data.",
        empty_message="No live-public structural edge snapshot is stored yet.",
    )

    left, right = st.columns((1, 1))
    with left:
        render_table_section(
            "Funding Snapshot",
            list(funding.get("rows") or []),
            subtitle="Latest stored funding-rate snapshot grouped as research-only carry context.",
            empty_message="No funding rows available.",
        )
        render_table_section(
            "Basis Snapshot",
            list(basis.get("rows") or []),
            subtitle="Latest stored perp/spot basis snapshot in the research store.",
            empty_message="No basis rows available.",
        )

    with right:
        render_table_section(
            "Cross-Venue Dislocations",
            list(dislocations.get("rows") or []),
            subtitle="Latest stored quote snapshot ranked by gross bid/ask dislocation. Source filters apply to provenance and history panels below.",
            empty_message="No quote dislocation rows available.",
        )
        render_table_section(
            "Recent Snapshot History",
            history_rows,
            subtitle="Recent funding, basis, and quote ingests grouped by snapshot id and source, filtered by the controls above.",
            empty_message="No snapshot history available.",
        )

    trend_left, trend_right = st.columns((1, 1))
    with trend_left:
        render_table_section(
            "Funding History",
            funding_history,
            subtitle="Recent funding carry summaries rebuilt from stored snapshots.",
            empty_message="No funding history available.",
        )
        render_table_section(
            "Basis History",
            basis_history,
            subtitle="Recent basis summaries rebuilt from stored snapshots.",
            empty_message="No basis history available.",
        )

    with trend_right:
        render_table_section(
            "Dislocation History",
            dislocation_history,
            subtitle="Recent cross-venue dislocation summaries rebuilt from stored quote snapshots.",
            empty_message="No dislocation history available.",
        )
