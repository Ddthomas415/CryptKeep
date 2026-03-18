from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.components.cards import render_feature_hero, render_kpi_cards, render_prompt_actions
from dashboard.components.header import render_page_header
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.tables import render_table_section
from dashboard.services.crypto_edge_research import load_crypto_edge_workspace

AUTH_STATE = require_authenticated_role("VIEWER")
render_app_sidebar()

workspace = load_crypto_edge_workspace()
render_page_header(
    "Research",
    "Crypto-native structural edge workspace for funding, basis, and cross-venue dislocation analysis.",
    badges=[
        {"label": "Mode", "value": "Research Only"},
        {"label": "Data", "value": "Stored Snapshots" if bool(workspace.get("has_any_data")) else "No Snapshots"},
    ],
)

render_feature_hero(
    eyebrow="Structural Edge Workspace",
    title="Funding Carry, Basis, and Cross-Venue Dislocations",
    summary=(
        "Use stored snapshots to review crypto-native market structure without coupling this research to execution."
    ),
    body=(
        "Load bundled sample data with `make load-sample-crypto-edges` or ingest your own JSON snapshots with "
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
            "label": "Store",
            "value": "Ready" if bool(workspace.get("has_any_data")) else "Empty",
            "delta": str(workspace.get("store_path") or "unavailable"),
        },
    ],
    aside_title="Ask Copilot",
    aside_lines=[
        "Summarize funding carry state",
        "Explain current basis structure",
        "Show top cross-venue dislocations",
        "What changed while I was away?",
    ],
)

render_prompt_actions(
    title="Copilot Shortcuts",
    prompts=[
        "Summarize funding carry state",
        "Explain current basis structure",
        "Show top cross-venue dislocations",
        "What changed while I was away?",
    ],
    key_prefix="research",
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
        subtitle="Latest stored quote snapshot ranked by gross bid/ask dislocation.",
        empty_message="No quote dislocation rows available.",
    )
    render_table_section(
        "Recent Snapshot History",
        list(workspace.get("history_rows") or []),
        subtitle="Recent funding, basis, and quote ingests grouped by snapshot id and source.",
        empty_message="No snapshot history available.",
    )
