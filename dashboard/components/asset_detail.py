from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.components.badges import render_badge_row
from dashboard.components.tables import render_table_section


def _format_currency(value: Any) -> str:
    try:
        amount = float(value or 0.0)
    except (TypeError, ValueError):
        return "-"
    if amount <= 0:
        return "-"
    return f"${amount:,.2f}"


def _format_reasoning_provider(value: Any) -> str:
    provider = str(value or "").strip().lower()
    if not provider:
        return ""
    if provider == "openai":
        return "OpenAI"
    if provider == "backend_api":
        return "Backend API"
    if provider == "phase1_copilot":
        return "Phase 1 Copilot"
    if provider == "dashboard_fallback":
        return "Dashboard Fallback"
    if provider == "gateway_fallback":
        return "Gateway Fallback"
    return provider.replace("_", " ").title()


def build_assistant_status_summary(detail: dict[str, Any] | None) -> str:
    payload = detail if isinstance(detail, dict) else {}
    assistant_status = (
        payload.get("assistant_status") if isinstance(payload.get("assistant_status"), dict) else {}
    )
    if not assistant_status:
        return ""

    provider = _format_reasoning_provider(assistant_status.get("provider"))
    model = str(assistant_status.get("model") or "").strip()
    fallback = bool(assistant_status.get("fallback"))

    parts = [part for part in (provider, model) if part]
    if not parts:
        return ""

    summary = f"Reasoning: {' | '.join(parts)}"
    if fallback:
        summary = f"{summary} | fallback"
    return summary


def build_assistant_status_message(detail: dict[str, Any] | None) -> str:
    payload = detail if isinstance(detail, dict) else {}
    assistant_status = (
        payload.get("assistant_status") if isinstance(payload.get("assistant_status"), dict) else {}
    )
    message = str(assistant_status.get("message") or "").strip()
    return message


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


def build_focus_summary_metrics(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = detail if isinstance(detail, dict) else {}
    try:
        confidence = float(payload.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    try:
        change_24h_pct = float(payload.get("change_24h_pct") or 0.0)
    except (TypeError, ValueError):
        change_24h_pct = 0.0

    signal_value = str(payload.get("signal") or "watch").replace("_", " ").title()
    signal_delta = str(payload.get("status") or "monitor").replace("_", " ").title()
    execution_state = str(payload.get("execution_state") or "").strip()
    if execution_state:
        execution_value = str(payload.get("status") or "monitor").replace("_", " ").title()
        execution_delta = execution_state
    else:
        execution_value = "Disabled" if bool(payload.get("execution_disabled", True)) else "Enabled"
        execution_delta = str(payload.get("risk_note") or "").strip()

    return [
        {
            "label": "Signal",
            "value": signal_value,
            "delta": signal_delta,
        },
        {
            "label": "Confidence",
            "value": f"{confidence * 100:.0f}%",
            "delta": "AI conviction",
        },
        {
            "label": "24h Move",
            "value": f"{change_24h_pct:+.1f}%",
            "delta": _format_currency(payload.get("price")),
        },
        {
            "label": "Execution",
            "value": execution_value,
            "delta": execution_delta,
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
        detail_badges: list[dict[str, str]] = []
        signal = str(payload.get("signal") or "").strip()
        status = str(payload.get("status") or "").strip()
        regime = str(payload.get("regime") or "").strip()
        category = str(payload.get("category") or "").strip()
        if signal:
            detail_badges.append({"text": signal.replace("_", " ").title(), "tone": "accent"})
        if status:
            detail_badges.append({"text": status.replace("_", " ").title(), "tone": "muted"})
        if regime:
            detail_badges.append({"text": regime.replace("_", " ").title(), "tone": "success"})
        if category:
            detail_badges.append({"text": category.replace("_", " ").title(), "tone": "warning"})
        render_badge_row(detail_badges)
        assistant_summary = build_assistant_status_summary(payload)
        if assistant_summary:
            st.caption(assistant_summary)
        assistant_message = build_assistant_status_message(payload)
        if assistant_message:
            st.caption(assistant_message)
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
            st.line_chart(price_series, width="stretch")
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
        research_badges: list[dict[str, str]] = []
        if str(payload.get("signal") or "").strip():
            research_badges.append(
                {"text": str(payload.get("signal") or "").replace("_", " ").title(), "tone": "accent"}
            )
        if str(payload.get("regime") or "").strip():
            research_badges.append(
                {"text": str(payload.get("regime") or "").replace("_", " ").title(), "tone": "success"}
            )
        if bool(payload.get("execution_disabled", True)):
            research_badges.append({"text": "Research Only", "tone": "warning"})
        render_badge_row(research_badges)
        assistant_summary = build_assistant_status_summary(payload)
        if assistant_summary:
            st.caption(assistant_summary)
        assistant_message = build_assistant_status_message(payload)
        if assistant_message:
            st.caption(assistant_message)
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
        metric_items = build_focus_summary_metrics(payload)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)
        assistant_summary = build_assistant_status_summary(payload)
        if assistant_summary:
            st.caption(assistant_summary)
        assistant_message = build_assistant_status_message(payload)
        if assistant_message:
            st.caption(assistant_message)
        st.caption(str(payload.get("current_cause") or payload.get("thesis") or empty_message))
        secondary = str(payload.get("future_catalyst") or "").strip()
        if secondary:
            st.caption(f"{secondary_label}: {secondary}")
        risk_note = str(payload.get("risk_note") or "").strip()
        if risk_note:
            st.caption(risk_note)
