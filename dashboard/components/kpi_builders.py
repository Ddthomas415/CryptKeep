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
            "label": "Volume Trend",
            "value": str(payload.get("volume_trend") or "steady").title(),
            "delta": "Watchlist context",
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
