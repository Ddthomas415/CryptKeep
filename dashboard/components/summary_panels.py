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


def _format_portfolio_currency(value: Any) -> str:
    try:
        amount = float(value or 0.0)
    except (TypeError, ValueError):
        return "$0.00"
    return f"${amount:,.2f}"


def build_portfolio_position_metrics(rows: Sequence[dict[str, Any]] | None) -> list[dict[str, str]]:
    positions = [row for row in (rows or []) if isinstance(row, dict)]
    if not positions:
        return [
            {"label": "Open Positions", "value": "0", "delta": "No active exposure"},
            {"label": "Long / Short", "value": "0 / 0", "delta": "Position mix"},
            {"label": "Best PnL", "value": "-", "delta": "No active position"},
            {"label": "Worst PnL", "value": "-", "delta": "No active position"},
        ]

    long_count = sum(1 for row in positions if str(row.get("side") or "").strip().lower() == "long")
    short_count = sum(1 for row in positions if str(row.get("side") or "").strip().lower() == "short")
    best = max(positions, key=lambda row: float(row.get("pnl") or 0.0))
    worst = min(positions, key=lambda row: float(row.get("pnl") or 0.0))

    return [
        {
            "label": "Open Positions",
            "value": str(len(positions)),
            "delta": "Active book",
        },
        {
            "label": "Long / Short",
            "value": f"{long_count} / {short_count}",
            "delta": "Position mix",
        },
        {
            "label": "Best PnL",
            "value": _format_portfolio_currency(best.get("pnl")),
            "delta": str(best.get("asset") or "-"),
        },
        {
            "label": "Worst PnL",
            "value": _format_portfolio_currency(worst.get("pnl")),
            "delta": str(worst.get("asset") or "-"),
        },
    ]


def render_portfolio_position_summary(rows: Sequence[dict[str, Any]] | None) -> None:
    with st.container(border=True):
        st.markdown("### Position Summary")
        metric_items = build_portfolio_position_metrics(rows)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)


def build_trades_queue_metrics(
    pending_approvals: Sequence[dict[str, Any]] | None,
    recent_fills: Sequence[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    approvals = [row for row in (pending_approvals or []) if isinstance(row, dict)]
    fills = [row for row in (recent_fills or []) if isinstance(row, dict)]
    buy_count = sum(1 for row in approvals if str(row.get("side") or "").strip().lower() == "buy")
    sell_count = sum(1 for row in approvals if str(row.get("side") or "").strip().lower() == "sell")
    latest_fill = fills[0] if fills else {}

    largest_review = max((float(row.get("risk_size_pct") or 0.0) for row in approvals), default=0.0)
    largest_asset = (
        str(max(approvals, key=lambda row: float(row.get("risk_size_pct") or 0.0)).get("asset") or "-")
        if approvals
        else "No queued trades"
    )

    return [
        {
            "label": "Approval Mix",
            "value": f"{buy_count} / {sell_count}",
            "delta": "Buy / Sell",
        },
        {
            "label": "Largest Review",
            "value": f"{largest_review:.1f}%",
            "delta": largest_asset,
        },
        {
            "label": "Last Fill Price",
            "value": _format_portfolio_currency(latest_fill.get("price")) if fills else "-",
            "delta": str(latest_fill.get("asset") or "No fills yet") if fills else "No fills yet",
        },
        {
            "label": "Last Fill Qty",
            "value": f"{float(latest_fill.get('qty') or 0.0):g}" if fills else "-",
            "delta": str(latest_fill.get("side") or "").upper() if fills else "No fills yet",
        },
    ]


def render_trades_queue_summary(
    pending_approvals: Sequence[dict[str, Any]] | None,
    recent_fills: Sequence[dict[str, Any]] | None,
) -> None:
    with st.container(border=True):
        st.markdown("### Execution Summary")
        metric_items = build_trades_queue_metrics(pending_approvals, recent_fills)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)


def build_automation_runtime_metrics(view: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = view if isinstance(view, dict) else {}
    return [
        {
            "label": "Runtime Mode",
            "value": str(payload.get("executor_mode") or "paper").upper(),
            "delta": "Live armed" if bool(payload.get("live_enabled")) else "Live disarmed",
        },
        {
            "label": "Approval",
            "value": "Required" if bool(payload.get("approval_required_for_live")) else "Optional",
            "delta": "Keys required" if bool(payload.get("require_keys_for_live", True)) else "Keys optional",
        },
        {
            "label": "Signal Defaults",
            "value": str(payload.get("default_venue") or "coinbase").upper(),
            "delta": f"qty {float(payload.get('default_qty') or 0.0):g} / {str(payload.get('order_type') or 'market')}",
        },
        {
            "label": "Paper Costs",
            "value": f"{float(payload.get('paper_fee_bps') or 0.0):g} / {float(payload.get('paper_slippage_bps') or 0.0):g} bps",
            "delta": f"max {int(payload.get('executor_max_per_cycle') or 0)} intents/cycle",
        },
    ]


def render_automation_runtime_summary(view: dict[str, Any] | None) -> None:
    payload = view if isinstance(view, dict) else {}
    with st.container(border=True):
        st.markdown("### Runtime Summary")
        metric_items = build_automation_runtime_metrics(payload)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)
