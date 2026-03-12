from __future__ import annotations

from dashboard.components.summary_panels import (
    build_automation_runtime_metrics,
    build_market_context_metrics,
    build_market_snapshot_lines,
    build_operations_status_metrics,
    build_overview_status_metrics,
    build_portfolio_position_metrics,
    build_settings_profile_metrics,
    build_trades_queue_metrics,
    resolve_asset_row,
)


def test_resolve_asset_row_returns_matching_asset() -> None:
    rows = [
        {"asset": "BTC", "summary": "Range trade"},
        {"asset": "SOL", "summary": "Momentum"},
    ]
    payload = resolve_asset_row(rows, asset="SOL")
    assert payload["summary"] == "Momentum"


def test_resolve_asset_row_returns_empty_dict_when_missing() -> None:
    rows = [{"asset": "BTC", "summary": "Range trade"}]
    payload = resolve_asset_row(rows, asset="ETH")
    assert payload == {}


def test_build_market_snapshot_lines_formats_quote_and_source() -> None:
    lines = build_market_snapshot_lines(
        {
            "price": 90555.25,
            "bid": 90550.0,
            "ask": 90560.5,
            "spread": 10.5,
            "exchange": "coinbase",
            "snapshot_source": "api",
            "snapshot_timestamp": "2026-03-11T12:55:00Z",
        },
        include_price=True,
    )

    assert lines[0] == "Spot: $90,555.25"
    assert lines[1] == "Quote: Bid $90,550.00 | Ask $90,560.50 | Spread $10.50"
    assert lines[2] == "Source: coinbase / api | 2026-03-11T12:55:00Z"


def test_build_market_context_metrics_include_snapshot_metadata() -> None:
    metrics = build_market_context_metrics(
        {
            "support": 89196.92,
            "resistance": 91913.58,
            "bid": 90550.0,
            "ask": 90560.5,
            "spread": 10.5,
            "exchange": "coinbase",
            "snapshot_source": "local_ws",
            "evidence": "Spot demand improved.",
        }
    )

    assert metrics[0] == {
        "label": "Support",
        "value": "$89,196.92",
        "delta": "buy-side reference",
    }
    assert metrics[1] == {
        "label": "Resistance",
        "value": "$91,913.58",
        "delta": "sell-side reference",
    }
    assert metrics[2] == {
        "label": "Bid / Ask",
        "value": "$90,550.00 / $90,560.50",
        "delta": "Spread $10.50",
    }
    assert metrics[3] == {
        "label": "Source",
        "value": "Local Ws",
        "delta": "coinbase",
    }


def test_build_overview_status_metrics_formats_workspace_state() -> None:
    metrics = build_overview_status_metrics(
        {
            "risk_status": "danger",
            "kill_switch": True,
            "blocked_trades_count": 3,
            "active_warnings": ["kill_switch_armed", "drawdown_warn"],
            "connections": {
                "connected_exchanges": 2,
                "connected_providers": 3,
                "failed": 1,
                "last_sync": "2026-03-12T10:05:00Z",
            },
            "portfolio": {
                "exposure_used_pct": 55.5,
                "leverage": 2.1,
            },
        }
    )

    assert metrics[0] == {
        "label": "Risk State",
        "value": "Danger",
        "delta": "kill_switch_armed, drawdown_warn",
    }
    assert metrics[1] == {
        "label": "Kill Switch",
        "value": "Armed",
        "delta": "Blocked 3 trades",
    }
    assert metrics[2] == {
        "label": "Connectivity",
        "value": "2 exch / 3 svc",
        "delta": "Failed 1",
    }
    assert metrics[3] == {
        "label": "Exposure",
        "value": "55.5%",
        "delta": "Leverage 2.1x",
    }


def test_build_operations_status_metrics_formats_service_state() -> None:
    metrics = build_operations_status_metrics(
        {
            "services": ["tick_publisher", "intent_executor", "audit_tail"],
            "tracked_services": 3,
            "healthy_services": 2,
            "attention_services": 1,
            "unknown_services": 0,
            "last_health_ts": "2026-03-12T10:05:00Z",
        }
    )

    assert metrics[0] == {
        "label": "Tracked Services",
        "value": "3",
        "delta": "tick_publisher, intent_executor +1",
    }
    assert metrics[1] == {
        "label": "Healthy",
        "value": "2",
        "delta": "2026-03-12T10:05:00Z",
    }
    assert metrics[2] == {
        "label": "Attention",
        "value": "1",
        "delta": "Needs review",
    }
    assert metrics[3] == {
        "label": "Unknown",
        "value": "0",
        "delta": "All tracked services reporting",
    }


def test_build_portfolio_position_metrics_formats_best_and_worst_positions() -> None:
    metrics = build_portfolio_position_metrics(
        [
            {"asset": "BTC", "side": "long", "pnl": 495.6},
            {"asset": "SOL", "side": "long", "pnl": 630.9},
            {"asset": "ETH", "side": "short", "pnl": -120.5},
        ]
    )

    assert metrics[0] == {
        "label": "Open Positions",
        "value": "3",
        "delta": "Active book",
    }
    assert metrics[1] == {
        "label": "Long / Short",
        "value": "2 / 1",
        "delta": "Position mix",
    }
    assert metrics[2] == {
        "label": "Best PnL",
        "value": "$630.90",
        "delta": "SOL",
    }
    assert metrics[3] == {
        "label": "Worst PnL",
        "value": "$-120.50",
        "delta": "ETH",
    }


def test_build_trades_queue_metrics_formats_queue_and_fill_details() -> None:
    metrics = build_trades_queue_metrics(
        [
            {"asset": "SOL", "side": "buy", "risk_size_pct": 1.5},
            {"asset": "BTC", "side": "sell", "risk_size_pct": 0.8},
        ],
        [
            {"asset": "BTC", "status": "open"},
        ],
        [
            {"asset": "ADA", "status": "failed"},
        ],
        [
            {"asset": "ETH", "side": "sell", "qty": 0.3, "price": 4390.0},
        ],
    )

    assert metrics[0] == {
        "label": "Approval Mix",
        "value": "1 / 1",
        "delta": "Buy / Sell",
    }
    assert metrics[1] == {
        "label": "Largest Review",
        "value": "1.5%",
        "delta": "SOL",
    }
    assert metrics[2] == {
        "label": "Open Orders",
        "value": "1",
        "delta": "BTC / Open",
    }
    assert metrics[3] == {
        "label": "Last Fill",
        "value": "$4,390.00",
        "delta": "ETH / SELL 0.3",
    }
    assert metrics[4] == {
        "label": "Failures",
        "value": "1",
        "delta": "ADA / Failed",
    }


def test_build_automation_runtime_metrics_format_runtime_state() -> None:
    metrics = build_automation_runtime_metrics(
        {
            "executor_mode": "live",
            "live_enabled": True,
            "approval_required_for_live": True,
            "require_keys_for_live": True,
            "default_venue": "coinbase",
            "default_qty": 0.25,
            "order_type": "limit",
            "paper_fee_bps": 9.0,
            "paper_slippage_bps": 4.0,
            "executor_max_per_cycle": 25,
        }
    )

    assert metrics[0] == {
        "label": "Runtime Mode",
        "value": "LIVE",
        "delta": "Live armed",
    }
    assert metrics[1] == {
        "label": "Approval",
        "value": "Required",
        "delta": "Keys required",
    }
    assert metrics[2] == {
        "label": "Signal Defaults",
        "value": "COINBASE",
        "delta": "qty 0.25 / limit",
    }
    assert metrics[3] == {
        "label": "Paper Costs",
        "value": "9 / 4 bps",
        "delta": "max 25 intents/cycle",
    }


def test_build_settings_profile_metrics_formats_workspace_profile() -> None:
    metrics = build_settings_profile_metrics(
        {
            "general": {
                "watchlist_defaults": ["BTC", "ETH", "SOL"],
            },
            "notifications": {
                "email": False,
                "telegram": True,
                "discord": False,
                "webhook": True,
            },
            "ai": {
                "tone": "balanced",
                "explanation_length": "normal",
            },
            "security": {
                "secret_masking": True,
                "audit_export_allowed": True,
            },
        }
    )

    assert metrics[0] == {
        "label": "Watchlist Defaults",
        "value": "3",
        "delta": "BTC, ETH, SOL",
    }
    assert metrics[1] == {
        "label": "Alert Targets",
        "value": "Telegram, Webhook",
        "delta": "Channels enabled",
    }
    assert metrics[2] == {
        "label": "AI Profile",
        "value": "Balanced",
        "delta": "Normal",
    }
    assert metrics[3] == {
        "label": "Security",
        "value": "Masked",
        "delta": "Audit export on",
    }
