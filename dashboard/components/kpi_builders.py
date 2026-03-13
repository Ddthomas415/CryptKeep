from __future__ import annotations

from typing import Any


def _format_currency(value: Any) -> str:
    return f"${float(value or 0.0):,.2f}"


def _format_pct(value: Any) -> str:
    return f"{float(value or 0.0):+.1f}%"


def _format_confidence(value: Any) -> str:
    return f"{float(value or 0.0) * 100:.0f}%"


def build_overview_kpis(
    *,
    portfolio: dict[str, Any] | None,
    signal_count: int,
    execution_enabled: bool,
) -> list[dict[str, str]]:
    payload = portfolio if isinstance(portfolio, dict) else {}
    return [
        {
            "label": "Portfolio Value",
            "value": _format_currency(payload.get("total_value")),
            "delta": f"Cash {_format_currency(payload.get('cash'))}",
        },
        {
            "label": "Unrealized PnL",
            "value": _format_currency(payload.get("unrealized_pnl")),
            "delta": "Live mark-to-market",
        },
        {
            "label": "Active Signals",
            "value": str(max(0, int(signal_count))),
            "delta": "Recommendation set",
        },
        {
            "label": "Bot Status",
            "value": "Running" if execution_enabled else "Research Only",
            "delta": "Automation enabled" if execution_enabled else "Execution disabled",
        },
    ]


def build_markets_kpis(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = detail if isinstance(detail, dict) else {}
    return [
        {
            "label": "Last Price",
            "value": _format_currency(payload.get("price")),
            "delta": f"24h {_format_pct(payload.get('change_24h_pct'))}",
        },
        {
            "label": "Signal State",
            "value": str(payload.get("signal") or "watch").replace("_", " ").title(),
            "delta": str(payload.get("status") or "monitor").replace("_", " ").title(),
        },
        {
            "label": "Confidence",
            "value": _format_confidence(payload.get("confidence")),
            "delta": "AI conviction",
        },
        {
            "label": "Opportunity",
            "value": str(payload.get("category") or "needs_confirmation").replace("_", " ").title(),
            "delta": f"Score {_format_confidence(payload.get('opportunity_score'))} / {str(payload.get('regime') or 'unknown').replace('_', ' ').title()}",
        },
    ]


def build_signals_kpis(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = detail if isinstance(detail, dict) else {}
    return [
        {
            "label": "Signal",
            "value": str(payload.get("signal") or "watch").replace("_", " ").title(),
            "delta": str(payload.get("status") or "monitor").replace("_", " ").title(),
        },
        {
            "label": "Confidence",
            "value": _format_confidence(payload.get("confidence")),
            "delta": "AI conviction",
        },
        {
            "label": "Opportunity",
            "value": str(payload.get("category") or "needs_confirmation").replace("_", " ").title(),
            "delta": f"Score {_format_confidence(payload.get('opportunity_score'))} / {str(payload.get('regime') or 'unknown').replace('_', ' ').title()}",
        },
        {
            "label": "24h Change",
            "value": _format_pct(payload.get("change_24h_pct")),
            "delta": _format_currency(payload.get("price")),
        },
        {
            "label": "Execution",
            "value": "Disabled" if bool(payload.get("execution_disabled", True)) else "Enabled",
            "delta": str(payload.get("risk_note") or "Policy managed"),
        },
    ]


def build_trades_kpis(
    *,
    approval_required: bool,
    pending_approvals: list[dict[str, Any]] | None,
    open_orders: list[dict[str, Any]] | None,
    failed_orders: list[dict[str, Any]] | None,
    recent_fills: list[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    approvals = pending_approvals if isinstance(pending_approvals, list) else []
    orders = open_orders if isinstance(open_orders, list) else []
    failures = failed_orders if isinstance(failed_orders, list) else []
    fills = recent_fills if isinstance(recent_fills, list) else []
    lead_approval = approvals[0] if approvals else {}
    lead_order = orders[0] if orders else {}
    lead_failure = failures[0] if failures else {}
    latest_fill = fills[0] if fills else {}

    return [
        {
            "label": "Safety",
            "value": "Approval Required" if approval_required else "Auto Approved",
            "delta": "Review gate active" if approval_required else "Execution can auto-route",
        },
        {
            "label": "Pending Approvals",
            "value": str(len(approvals)),
            "delta": str(lead_approval.get("asset") or "Queue clear") if approvals else "Queue clear",
        },
        {
            "label": "Open Orders",
            "value": str(len(orders)),
            "delta": f"{str(lead_order.get('asset') or '-')} / {str(lead_order.get('status') or '').replace('_', ' ').title()}".strip(" /")
            if orders
            else "No open orders",
        },
        {
            "label": "Recent Fills",
            "value": str(len(fills)),
            "delta": str(latest_fill.get("asset") or "No fills yet") if fills else "No fills yet",
        },
        {
            "label": "Failed Orders",
            "value": str(len(failures)),
            "delta": (
                f"{str(lead_failure.get('asset') or '-')} / {str(lead_failure.get('status') or '').replace('_', ' ').title()}"
            ).strip(" /")
            if failures
            else "No failures",
        },
    ]


def build_portfolio_kpis(
    *,
    portfolio: dict[str, Any] | None,
    positions: list[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    payload = portfolio if isinstance(portfolio, dict) else {}
    rows = positions if isinstance(positions, list) else []
    return [
        {
            "label": "Total Value",
            "value": _format_currency(payload.get("total_value")),
            "delta": f"Cash {_format_currency(payload.get('cash'))}",
        },
        {
            "label": "Unrealized PnL",
            "value": _format_currency(payload.get("unrealized_pnl")),
            "delta": "Live mark-to-market",
        },
        {
            "label": "Exposure Used",
            "value": _format_pct(payload.get("exposure_used_pct")).replace("+", ""),
            "delta": f"Leverage {float(payload.get('leverage') or 1.0):.1f}x",
        },
        {
            "label": "Open Positions",
            "value": str(len(rows)),
            "delta": "Tracked book",
        },
    ]


def build_automation_kpis(view: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = view if isinstance(view, dict) else {}
    execution_enabled = bool(payload.get("execution_enabled"))
    dry_run_mode = bool(payload.get("dry_run_mode"))
    default_mode = str(payload.get("default_mode") or "research_only").replace("_", " ").title()
    schedule = str(payload.get("schedule") or "manual").title()
    routing = str(payload.get("marketplace_routing") or "disabled").title()

    return [
        {
            "label": "Execution",
            "value": "Enabled" if execution_enabled else "Disabled",
            "delta": "Dry run active" if dry_run_mode else "Live path available",
        },
        {
            "label": "Default Mode",
            "value": default_mode,
            "delta": str(payload.get("executor_mode") or "paper").upper(),
        },
        {
            "label": "Schedule",
            "value": schedule,
            "delta": f"Poll {float(payload.get('executor_poll_sec') or 0.0):g}s",
        },
        {
            "label": "Routing",
            "value": routing,
            "delta": "Approval gated" if bool(payload.get("approval_required_for_live")) else "Approval optional",
        },
    ]


def build_settings_kpis(view: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = view if isinstance(view, dict) else {}
    general = payload.get("general") if isinstance(payload.get("general"), dict) else {}
    notifications = payload.get("notifications") if isinstance(payload.get("notifications"), dict) else {}
    ai = payload.get("ai") if isinstance(payload.get("ai"), dict) else {}
    autopilot = payload.get("autopilot") if isinstance(payload.get("autopilot"), dict) else {}
    providers = payload.get("providers") if isinstance(payload.get("providers"), dict) else {}
    security = payload.get("security") if isinstance(payload.get("security"), dict) else {}
    categories = notifications.get("categories") if isinstance(notifications.get("categories"), dict) else {}

    enabled_notifications = sum(
        1 for value in categories.values() if isinstance(value, bool) and value
    )
    enabled_providers = sum(
        1 for value in providers.values() if isinstance(value, dict) and bool(value.get("enabled"))
    )

    return [
        {
            "label": "Workspace",
            "value": str(general.get("timezone") or "UTC"),
            "delta": str(general.get("default_mode") or "research_only").replace("_", " ").title(),
        },
        {
            "label": "Alerts",
            "value": str(notifications.get("delivery_mode") or "instant").replace("_", " ").title(),
            "delta": f"{enabled_notifications} active categories",
        },
        {
            "label": "Copilot",
            "value": str(ai.get("tone") or "balanced").title(),
            "delta": str(ai.get("autopilot_explanation_depth") or "standard").replace("_", " ").title(),
        },
        {
            "label": "Scout",
            "value": "Enabled" if bool(autopilot.get("autopilot_enabled")) else "Ready",
            "delta": f"{int(autopilot.get('candidate_limit') or 0)} candidates / {int(autopilot.get('scan_interval_minutes') or 0)}m",
        },
        {
            "label": "Providers",
            "value": str(enabled_providers),
            "delta": "Enabled integrations",
        },
        {
            "label": "Session",
            "value": f"{int(security.get('session_timeout_minutes') or 60)} min",
            "delta": "Secret masking on" if bool(security.get("secret_masking", True)) else "Secret masking off",
        },
    ]
