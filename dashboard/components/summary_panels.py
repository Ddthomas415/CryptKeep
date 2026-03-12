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
        execution_state = str(selected_row.get("execution_state") or payload.get("execution_state") or "").strip()
        if execution_state:
            st.caption(f"Execution: {execution_state}")


def build_overview_status_metrics(summary: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = summary if isinstance(summary, dict) else {}
    portfolio = payload.get("portfolio") if isinstance(payload.get("portfolio"), dict) else {}
    connections = payload.get("connections") if isinstance(payload.get("connections"), dict) else {}
    warnings = payload.get("active_warnings") if isinstance(payload.get("active_warnings"), list) else []

    warning_preview = ", ".join(str(item) for item in warnings[:2]) if warnings else "No active warnings"
    failed_count = int(connections.get("failed") or 0)
    last_sync = str(connections.get("last_sync") or "").strip()
    connectivity_delta = f"Failed {failed_count}" if failed_count else (last_sync or "No sync recorded")

    return [
        {
            "label": "Risk State",
            "value": str(payload.get("risk_status") or "safe").replace("_", " ").title(),
            "delta": warning_preview,
        },
        {
            "label": "Kill Switch",
            "value": "Armed" if bool(payload.get("kill_switch")) else "Off",
            "delta": f"Blocked {int(payload.get('blocked_trades_count') or 0)} trades",
        },
        {
            "label": "Connectivity",
            "value": f"{int(connections.get('connected_exchanges') or 0)} exch / {int(connections.get('connected_providers') or 0)} svc",
            "delta": connectivity_delta,
        },
        {
            "label": "Exposure",
            "value": f"{float(portfolio.get('exposure_used_pct') or 0.0):.1f}%",
            "delta": f"Leverage {float(portfolio.get('leverage') or 0.0):.1f}x",
        },
    ]


def render_overview_status_summary(summary: dict[str, Any] | None) -> None:
    with st.container(border=True):
        st.markdown("### Workspace Status")
        metric_items = build_overview_status_metrics(summary)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)


def build_operations_status_metrics(snapshot: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = snapshot if isinstance(snapshot, dict) else {}
    services = payload.get("services") if isinstance(payload.get("services"), list) else []
    service_preview = ", ".join(str(item) for item in services[:2]) if services else "No services listed"
    if len(services) > 2:
        service_preview += f" +{len(services) - 2}"

    attention = int(payload.get("attention_services") or 0)
    unknown = int(payload.get("unknown_services") or 0)
    last_health_ts = str(payload.get("last_health_ts") or "").strip()

    return [
        {
            "label": "Tracked Services",
            "value": str(int(payload.get("tracked_services") or 0)),
            "delta": service_preview,
        },
        {
            "label": "Healthy",
            "value": str(int(payload.get("healthy_services") or 0)),
            "delta": last_health_ts or "No health timestamp",
        },
        {
            "label": "Attention",
            "value": str(attention),
            "delta": "Needs review" if attention else "No service errors",
        },
        {
            "label": "Unknown",
            "value": str(unknown),
            "delta": "Missing health state" if unknown else "All tracked services reporting",
        },
    ]


def render_operations_status_summary(snapshot: dict[str, Any] | None) -> None:
    payload = snapshot if isinstance(snapshot, dict) else {}
    with st.container(border=True):
        st.markdown("### Operations Status")
        metric_items = build_operations_status_metrics(payload)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)


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


def build_settings_profile_metrics(view: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = view if isinstance(view, dict) else {}
    general = payload.get("general") if isinstance(payload.get("general"), dict) else {}
    notifications = payload.get("notifications") if isinstance(payload.get("notifications"), dict) else {}
    ai = payload.get("ai") if isinstance(payload.get("ai"), dict) else {}
    security = payload.get("security") if isinstance(payload.get("security"), dict) else {}

    watchlist_defaults = general.get("watchlist_defaults") if isinstance(general.get("watchlist_defaults"), list) else []
    alert_targets = [
        name
        for name in ("email", "telegram", "discord", "webhook")
        if bool(notifications.get(name))
    ]
    alert_target_value = ", ".join(alert_targets[:2]).title() if alert_targets else "None"
    if len(alert_targets) > 2:
        alert_target_value += f" +{len(alert_targets) - 2}"

    return [
        {
            "label": "Watchlist Defaults",
            "value": str(len(watchlist_defaults)),
            "delta": ", ".join(str(item) for item in watchlist_defaults[:3]) or "No defaults",
        },
        {
            "label": "Alert Targets",
            "value": alert_target_value,
            "delta": "Channels enabled",
        },
        {
            "label": "AI Profile",
            "value": str(ai.get("tone") or "balanced").title(),
            "delta": str(ai.get("explanation_length") or "normal").title(),
        },
        {
            "label": "Security",
            "value": "Masked" if bool(security.get("secret_masking", True)) else "Visible",
            "delta": "Audit export on" if bool(security.get("audit_export_allowed", True)) else "Audit export off",
        },
    ]


def render_settings_profile_summary(view: dict[str, Any] | None) -> None:
    payload = view if isinstance(view, dict) else {}
    with st.container(border=True):
        st.markdown("### Settings Profile")
        metric_items = build_settings_profile_metrics(payload)
        metric_cols = st.columns(len(metric_items))
        for col, item in zip(metric_cols, metric_items, strict=False):
            with col:
                with st.container(border=True):
                    st.caption(str(item.get("label") or ""))
                    st.markdown(f"**{str(item.get('value') or '-')}**")
                    delta = str(item.get("delta") or "").strip()
                    if delta:
                        st.caption(delta)
