from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.components.tables import render_table_section


def _format_currency(value: Any) -> str:
    try:
        amount = float(value or 0.0)
    except (TypeError, ValueError):
        return "-"
    if amount <= 0:
        return "-"
    return f"${amount:,.2f}"


def build_asset_detail_metrics(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = detail if isinstance(detail, dict) else {}
    exchange = str(payload.get("exchange") or "").strip()
    snapshot_source = str(payload.get("snapshot_source") or "").strip().replace("_", " ")
    snapshot_timestamp = str(payload.get("snapshot_timestamp") or "").strip()

    source_value = snapshot_source.title() if snapshot_source else "Watchlist"
    source_delta = " / ".join(part for part in (exchange, snapshot_timestamp) if part)

    return [
        {
            "label": "Spot",
            "value": _format_currency(payload.get("price")),
            "delta": exchange or "",
        },
        {
            "label": "Bid / Ask",
            "value": f"{_format_currency(payload.get('bid'))} / {_format_currency(payload.get('ask'))}",
            "delta": "",
        },
        {
            "label": "Spread",
            "value": _format_currency(payload.get("spread")),
            "delta": "",
        },
        {
            "label": "Source",
            "value": source_value,
            "delta": source_delta,
        },
    ]


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
        metric_items = build_asset_detail_metrics(payload)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)
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
