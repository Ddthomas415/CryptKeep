from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.components.tables import render_table_section


def render_asset_detail_card(
    detail: dict[str, Any] | None,
    *,
    title: str,
    fallback_asset: str = "Asset",
    empty_message: str = "No asset detail available.",
    footer: str | None = None,
) -> None:
    payload = detail if isinstance(detail, dict) else {}
    asset = str(payload.get("asset") or fallback_asset)
    primary_text = str(payload.get("current_cause") or payload.get("thesis") or empty_message)
    price_series = payload.get("price_series") if isinstance(payload.get("price_series"), list) else []

    st.markdown(f"### {title}")
    with st.container(border=True):
        st.markdown(f"#### {asset}")
        st.caption(primary_text)
        if price_series:
            st.line_chart(price_series, use_container_width=True)
        else:
            st.info("No price series available.")
        if footer:
            st.caption(footer)


def render_evidence_section(
    detail: dict[str, Any] | None,
    *,
    title: str = "Evidence",
    empty_message: str = "No supporting evidence available.",
) -> None:
    payload = detail if isinstance(detail, dict) else {}
    rows = payload.get("evidence_items") if isinstance(payload.get("evidence_items"), list) else []
    render_table_section(title, rows, empty_message=empty_message)


def render_research_lens(
    detail: dict[str, Any] | None,
    *,
    title: str = "Research Lens",
    question_fallback: str = "Why is this asset moving?",
) -> None:
    payload = detail if isinstance(detail, dict) else {}

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(str(payload.get("question") or question_fallback))
        st.markdown(
            f"**Current Cause**  \n{str(payload.get('current_cause') or 'No current-cause summary available.')}"
        )
        st.markdown(
            f"**Past Precedent**  \n{str(payload.get('past_precedent') or 'No historical precedent available.')}"
        )
        st.markdown(
            f"**Future Catalyst**  \n{str(payload.get('future_catalyst') or 'No forward catalyst available.')}"
        )
        risk_note = str(payload.get("risk_note") or "").strip()
        if risk_note:
            st.caption(risk_note)


def render_focus_summary(
    detail: dict[str, Any] | None,
    *,
    title: str = "Focused Signal",
    empty_message: str = "No focused signal detail available.",
    secondary_label: str = "Future catalyst",
) -> None:
    payload = detail if isinstance(detail, dict) else {}

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(str(payload.get("current_cause") or payload.get("thesis") or empty_message))
        secondary = str(payload.get("future_catalyst") or "").strip()
        if secondary:
            st.caption(f"{secondary_label}: {secondary}")
        risk_note = str(payload.get("risk_note") or "").strip()
        if risk_note:
            st.caption(risk_note)
