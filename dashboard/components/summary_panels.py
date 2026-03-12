from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st


def resolve_asset_row(
    rows: Sequence[dict[str, Any]] | None,
    *,
    asset: str,
    asset_field: str = "asset",
) -> dict[str, Any]:
    target = str(asset or "")
    return next(
        (
            item
            for item in rows or []
            if isinstance(item, dict) and str(item.get(asset_field) or "") == target
        ),
        {},
    )


def build_market_snapshot_lines(
    detail: dict[str, Any] | None,
    *,
    include_price: bool = False,
) -> list[str]:
    payload = detail if isinstance(detail, dict) else {}
    lines: list[str] = []

    price = float(payload.get("price") or 0.0)
    if include_price and price > 0:
        lines.append(f"Spot: ${price:,.2f}")

    quote_parts: list[str] = []
    bid = float(payload.get("bid") or 0.0)
    ask = float(payload.get("ask") or 0.0)
    spread = float(payload.get("spread") or 0.0)
    if bid > 0:
        quote_parts.append(f"Bid ${bid:,.2f}")
    if ask > 0:
        quote_parts.append(f"Ask ${ask:,.2f}")
    if spread > 0:
        quote_parts.append(f"Spread ${spread:,.2f}")
    if quote_parts:
        lines.append("Quote: " + " | ".join(quote_parts))

    source_parts: list[str] = []
    exchange = str(payload.get("exchange") or "").strip()
    source = str(payload.get("snapshot_source") or "").strip().replace("_", " ")
    timestamp = str(payload.get("snapshot_timestamp") or "").strip()
    if exchange:
        source_parts.append(exchange)
    if source:
        source_parts.append(source)

    if source_parts or timestamp:
        meta = " / ".join(source_parts)
        if timestamp:
            meta = f"{meta} | {timestamp}" if meta else timestamp
        lines.append(f"Source: {meta}")

    return lines


def _format_currency(value: Any) -> str:
    try:
        amount = float(value or 0.0)
    except (TypeError, ValueError):
        return "-"
    if amount <= 0:
        return "-"
    return f"${amount:,.2f}"


def build_market_context_metrics(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = detail if isinstance(detail, dict) else {}
    exchange = str(payload.get("exchange") or "").strip()
    snapshot_source = str(payload.get("snapshot_source") or "").strip().replace("_", " ")
    snapshot_timestamp = str(payload.get("snapshot_timestamp") or "").strip()
    source_value = snapshot_source.title() if snapshot_source else "Watchlist"
    source_delta = " / ".join(part for part in (exchange, snapshot_timestamp) if part)

    return [
        {
            "label": "Support",
            "value": _format_currency(payload.get("support")),
            "delta": "buy-side reference",
        },
        {
            "label": "Resistance",
            "value": _format_currency(payload.get("resistance")),
            "delta": "sell-side reference",
        },
        {
            "label": "Bid / Ask",
            "value": f"{_format_currency(payload.get('bid'))} / {_format_currency(payload.get('ask'))}",
            "delta": f"Spread {_format_currency(payload.get('spread'))}"
            if _format_currency(payload.get("spread")) != "-"
            else "",
        },
        {
            "label": "Source",
            "value": source_value,
            "delta": source_delta,
        },
    ]


def render_market_context(detail: dict[str, Any] | None) -> None:
    payload = detail if isinstance(detail, dict) else {}
    with st.container(border=True):
        st.markdown("### Market Context")
        metric_items = build_market_context_metrics(payload)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)
        st.caption(f"Evidence: {str(payload.get('evidence') or 'No evidence available.')}")


def render_signal_thesis(
    rows: Sequence[dict[str, Any]] | None,
    detail: dict[str, Any] | None,
    *,
    fallback_asset: str,
) -> None:
    payload = detail if isinstance(detail, dict) else {}
    selected_row = resolve_asset_row(rows, asset=str(payload.get("asset") or fallback_asset))

    with st.container(border=True):
        st.markdown("### Signal Thesis")
        st.caption(
            str(selected_row.get("summary") or payload.get("current_cause") or "No signal thesis available.")
        )
        st.caption(
            f"Evidence: {str(selected_row.get('evidence') or payload.get('evidence') or 'No evidence available.')}"
        )
