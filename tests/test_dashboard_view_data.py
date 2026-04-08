from __future__ import annotations

from dashboard.services import view_data


def test_dashboard_summary_uses_defaults_when_sources_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda _path: None)
    monkeypatch.setattr(view_data, "_read_mock_envelope", lambda _name: None)
    monkeypatch.setattr(view_data, "_apply_local_summary_overrides", lambda summary: summary)

    summary = view_data.get_dashboard_summary()
    assert summary["mode"] == "research_only"
    assert summary["risk_status"] == "safe"
    assert float(summary["portfolio"]["total_value"]) > 0


def test_dashboard_summary_applies_local_runtime_overrides(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: {
            "status": "success",
            "data": {
                "mode": "research_only",
                "execution_enabled": False,
                "approval_required": True,
                "risk_status": "safe",
                "kill_switch": False,
                "portfolio": {
                    "total_value": 1000.0,
                    "cash": 300.0,
                    "unrealized_pnl": 25.0,
                },
                "watchlist": [{"asset": "BTC", "price": 90000.0}],
            },
        }
        if path == "/api/v1/dashboard/summary"
        else None,
    )
    monkeypatch.setattr(
        view_data,
        "_load_local_portfolio_snapshot",
        lambda _prices: {
            "portfolio": {
                "total_value": 1500.0,
                "cash": 450.0,
                "unrealized_pnl": 120.0,
            }
        },
    )
    monkeypatch.setattr(
        view_data,
        "load_user_yaml",
        lambda: {
            "execution": {"live_enabled": True},
            "dashboard_ui": {
                "automation": {
                    "enabled": True,
                    "default_mode": "live_auto",
                    "approval_required_for_live": False,
                }
            },
        },
    )
    monkeypatch.setattr(view_data, "_load_local_kill_switch_state", lambda: True)
    monkeypatch.setattr(view_data, "_load_local_system_guard_state", lambda: {"state": "HALTING", "writer": "watchdog", "reason": "stale"})
    monkeypatch.setattr(view_data, "_get_market_snapshot", lambda asset, exchange="coinbase": None)
    monkeypatch.setattr(view_data, "_load_local_connections_summary", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_risk_overlay", lambda portfolio_total_value=0.0: None)

    summary = view_data.get_dashboard_summary()
    assert summary["mode"] == "live_auto"
    assert summary["execution_enabled"] is True
    assert summary["approval_required"] is False
    assert summary["kill_switch"] is True
    assert summary["system_guard_state"] == "halting"
    assert summary["risk_status"] == "caution"
    assert "system_guard_halting" in summary["active_warnings"]
    assert summary["portfolio"]["total_value"] == 1500.0
    assert summary["portfolio"]["cash"] == 450.0


def test_dashboard_summary_prefers_local_watchlist_prices(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: {
            "status": "success",
            "data": {
                "mode": "research_only",
                "execution_enabled": False,
                "approval_required": True,
                "risk_status": "safe",
                "kill_switch": False,
                "portfolio": {"total_value": 1000.0, "cash": 300.0, "unrealized_pnl": 25.0},
                "watchlist": [{"asset": "BTC", "price": 80000.0, "change_24h_pct": 1.2, "signal": "watch"}],
            },
        }
        if path == "/api/v1/dashboard/summary"
        else None,
    )
    monkeypatch.setattr(view_data, "_load_local_portfolio_snapshot", lambda _prices: None)
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(view_data, "_load_local_kill_switch_state", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_system_guard_state", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_connections_summary", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_risk_overlay", lambda portfolio_total_value=0.0: None)
    monkeypatch.setattr(
        view_data,
        "_get_market_snapshot",
        lambda asset, exchange="coinbase": {
            "asset": asset,
            "exchange": exchange,
            "last_price": 90555.25,
            "source": "api",
            "volume_24h": 125000000.0,
        },
    )

    summary = view_data.get_dashboard_summary()
    assert summary["watchlist"][0]["asset"] == "BTC"
    assert summary["watchlist"][0]["price"] == 90555.25
    assert summary["watchlist"][0]["snapshot_source"] == "api"
    assert summary["watchlist"][0]["exchange"] == "coinbase"


def test_dashboard_summary_uses_settings_watchlist_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: {
            "status": "success",
            "data": {
                "mode": "research_only",
                "execution_enabled": False,
                "approval_required": True,
                "risk_status": "safe",
                "kill_switch": False,
                "portfolio": {"total_value": 1000.0, "cash": 300.0, "unrealized_pnl": 25.0},
                "watchlist": [],
            },
        }
        if path == "/api/v1/dashboard/summary"
        else None,
    )
    monkeypatch.setattr(view_data, "_load_local_portfolio_snapshot", lambda _prices: None)
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(view_data, "_load_local_kill_switch_state", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_system_guard_state", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_connections_summary", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_risk_overlay", lambda portfolio_total_value=0.0: None)
    monkeypatch.setattr(
        view_data,
        "get_settings_view",
        lambda: {"general": {"watchlist_defaults": ["BTC", "LINK"]}},
    )
    monkeypatch.setattr(
        view_data,
        "_get_market_snapshot",
        lambda asset, exchange="coinbase": {
            "asset": asset,
            "exchange": exchange,
            "last_price": 91000.0 if asset == "BTC" else 18.5,
            "source": "api",
        },
    )

    summary = view_data.get_dashboard_summary()
    assert [item["asset"] for item in summary["watchlist"]] == ["BTC", "LINK"]
    assert summary["watchlist"][0]["price"] == 91000.0
    assert summary["watchlist"][1]["price"] == 18.5
    assert summary["watchlist"][1]["signal"] == "watch"


def test_load_local_risk_overlay_uses_ops_gate_and_blocks(monkeypatch) -> None:
    class FakeOpsSignalStore:
        def latest_raw_signal(self):
            return {
                "drawdown_pct": 4.8,
                "exposure_usd": 420.0,
                "leverage": 1.4,
            }

        def latest_risk_gate(self):
            return {
                "gate_state": "ALLOW_ONLY_REDUCTIONS",
                "hazards": ["drawdown_warn"],
                "reasons": ["warn_threshold_breached"],
            }

    class FakeRiskBlocksStore:
        def last_n(self, limit: int = 200, run_id=None, venue=None, gate=None):
            assert limit == 20
            return [
                {"gate": "max_daily_loss", "reason": "daily loss hit"},
                {"gate": "max_daily_loss", "reason": "daily loss hit"},
            ]

    monkeypatch.setattr("storage.ops_signal_store_sqlite.OpsSignalStoreSQLite", FakeOpsSignalStore)
    monkeypatch.setattr("storage.risk_blocks_store_sqlite.RiskBlocksStoreSQLite", FakeRiskBlocksStore)
    monkeypatch.setattr(view_data, "_load_local_kill_switch_state", lambda: False)
    monkeypatch.setattr(view_data, "_load_local_system_guard_state", lambda: None)

    payload = view_data._load_local_risk_overlay(portfolio_total_value=1000.0)
    assert payload == {
        "risk_status": "caution",
        "blocked_trades_count": 2,
        "active_warnings": ["drawdown_warn", "warn_threshold_breached", "max_daily_loss"],
        "drawdown_today_pct": 4.8,
        "drawdown_week_pct": 4.8,
        "exposure_used_pct": 42.0,
        "leverage": 1.4,
    }


def test_load_local_connections_summary_uses_health_and_ws_state(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.admin.health.list_health",
        lambda: [
            {"service": "market_data", "status": "RUNNING", "ts": "2026-03-12T10:00:00Z"},
            {"service": "ops_risk_gate", "status": "RUNNING", "ts": "2026-03-12T10:01:00Z"},
            {"service": "evidence_webhook", "status": "ERROR", "ts": "2026-03-12T09:59:00Z"},
        ],
    )

    class FakeWSStatusStore:
        def recent_events(self, limit: int = 200):
            assert limit == 200
            return [
                {"exchange": "coinbase", "symbol": "BTC/USD", "status": "ok", "updated_ts": "2026-03-12T10:02:00Z"},
                {"exchange": "kraken", "symbol": "ETH/USD", "status": "error", "updated_ts": "2026-03-12T09:58:00Z"},
                {"exchange": "coinbase", "symbol": "ETH/USD", "status": "ok", "updated_ts": "2026-03-12T10:01:30Z"},
            ]

    monkeypatch.setattr("storage.ws_status_sqlite.WSStatusSQLite", FakeWSStatusStore)

    payload = view_data._load_local_connections_summary()
    assert payload == {
        "connected_exchanges": 1,
        "connected_providers": 2,
        "failed": 1,
        "last_sync": "2026-03-12T10:02:00Z",
    }


def test_dashboard_summary_applies_local_risk_overlay(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: {
            "status": "success",
            "data": {
                "mode": "research_only",
                "execution_enabled": False,
                "approval_required": True,
                "risk_status": "safe",
                "kill_switch": False,
                "portfolio": {
                    "total_value": 1000.0,
                    "cash": 300.0,
                    "unrealized_pnl": 25.0,
                    "exposure_used_pct": 18.4,
                    "leverage": 1.0,
                },
                "watchlist": [],
            },
        }
        if path == "/api/v1/dashboard/summary"
        else None,
    )
    monkeypatch.setattr(view_data, "_load_local_portfolio_snapshot", lambda _prices: None)
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(view_data, "_load_local_kill_switch_state", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_system_guard_state", lambda: {"state": "HALTED", "writer": "operator", "reason": "manual"})
    monkeypatch.setattr(view_data, "_load_local_connections_summary", lambda: None)
    monkeypatch.setattr(view_data, "get_settings_view", lambda: {"general": {"watchlist_defaults": []}})
    monkeypatch.setattr(view_data, "_get_market_snapshot", lambda asset, exchange="coinbase": None)
    monkeypatch.setattr(
        view_data,
        "_load_local_risk_overlay",
        lambda portfolio_total_value=0.0: {
            "risk_status": "danger",
            "blocked_trades_count": 3,
            "active_warnings": ["kill_switch_armed"],
            "drawdown_today_pct": 8.2,
            "drawdown_week_pct": 8.2,
            "exposure_used_pct": 55.5,
            "leverage": 2.1,
        },
    )

    summary = view_data.get_dashboard_summary()
    assert summary["risk_status"] == "danger"
    assert summary["blocked_trades_count"] == 3
    assert summary["active_warnings"] == ["kill_switch_armed", "system_guard_halted"]
    assert summary["system_guard_state"] == "halted"
    assert summary["drawdown_today_pct"] == 8.2
    assert summary["portfolio"]["exposure_used_pct"] == 55.5
    assert summary["portfolio"]["leverage"] == 2.1


def test_dashboard_summary_applies_local_connections_overlay(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: {
            "status": "success",
            "data": {
                "mode": "research_only",
                "execution_enabled": False,
                "approval_required": True,
                "risk_status": "safe",
                "kill_switch": False,
                "portfolio": {"total_value": 1000.0, "cash": 300.0, "unrealized_pnl": 25.0},
                "connections": {
                    "connected_exchanges": 0,
                    "connected_providers": 0,
                    "failed": 0,
                    "last_sync": None,
                },
                "watchlist": [],
            },
        }
        if path == "/api/v1/dashboard/summary"
        else None,
    )
    monkeypatch.setattr(view_data, "_load_local_portfolio_snapshot", lambda _prices: None)
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(view_data, "_load_local_kill_switch_state", lambda: None)
    monkeypatch.setattr(view_data, "_load_local_system_guard_state", lambda: None)
    monkeypatch.setattr(
        view_data,
        "_load_local_connections_summary",
        lambda: {
            "connected_exchanges": 2,
            "connected_providers": 3,
            "failed": 1,
            "last_sync": "2026-03-12T10:05:00Z",
        },
    )
    monkeypatch.setattr(view_data, "_load_local_risk_overlay", lambda portfolio_total_value=0.0: None)
    monkeypatch.setattr(view_data, "get_settings_view", lambda: {"general": {"watchlist_defaults": []}})
    monkeypatch.setattr(view_data, "_get_market_snapshot", lambda asset, exchange="coinbase": None)

    summary = view_data.get_dashboard_summary()
    assert summary["connections"] == {
        "connected_exchanges": 2,
        "connected_providers": 3,
        "failed": 1,
        "last_sync": "2026-03-12T10:05:00Z",
    }


def test_recommendations_map_api_payload(monkeypatch) -> None:
    payload = {
        "status": "success",
        "data": {
            "items": [
                {
                    "asset": "SOL",
                    "side": "buy",
                    "confidence": 0.74,
                    "strategy": "event_momentum",
                    "target_logic": "trailing",
                    "status": "pending_review",
                }
            ]
        },
    }

    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: payload if path == "/api/v1/trading/recommendations" else None,
    )
    monkeypatch.setattr(view_data, "_load_local_recommendations", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_pending_approvals", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_recent_fills", lambda limit=20: [])
    rows = view_data.get_recommendations()
    assert rows[0]["asset"] == "SOL"
    assert rows[0]["signal"] == "buy"
    assert rows[0]["status"] == "pending_review"


def test_recommendations_prefer_local_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_load_local_recommendations",
        lambda limit=20: [
            {
                "id": "sig_local_1",
                "asset": "ETH",
                "signal": "sell",
                "confidence": 0.67,
                "summary": "Inbox signal",
                "evidence": "source=tv",
                "status": "pending_review",
            }
        ],
    )
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda path: None)
    monkeypatch.setattr(view_data, "_load_local_pending_approvals", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_recent_fills", lambda limit=20: [])

    rows = view_data.get_recommendations()
    assert rows == [
        {
            "id": "sig_local_1",
            "asset": "ETH",
            "signal": "sell",
            "confidence": 0.67,
            "summary": "Inbox signal",
            "evidence": "source=tv",
            "status": "pending_review",
        }
    ]


def test_recommendations_overlay_local_execution_state(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_load_local_recommendations",
        lambda limit=20: [
            {
                "id": "sig_btc",
                "asset": "BTC",
                "signal": "buy",
                "confidence": 0.82,
                "summary": "Breakout held above support",
                "evidence": "tradingview",
                "status": "pending_review",
            },
            {
                "id": "sig_eth",
                "asset": "ETH",
                "signal": "sell",
                "confidence": 0.61,
                "summary": "Funding rolled over",
                "evidence": "partner_feed",
                "status": "pending_review",
            },
        ],
    )
    monkeypatch.setattr(
        view_data,
        "_load_local_pending_approvals",
        lambda limit=20: [
            {
                "asset": "BTC",
                "mode": "live",
                "venue": "coinbase",
                "order_type": "limit",
                "status": "queued",
            }
        ],
    )
    monkeypatch.setattr(
        view_data,
        "_load_local_recent_fills",
        lambda limit=20: [
            {
                "asset": "ETH",
                "side": "sell",
                "qty": 0.25,
                "price": 4420.0,
                "venue": "paper",
            }
        ],
    )
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda path: None)

    rows = view_data.get_recommendations()
    assert rows[0]["asset"] == "BTC"
    assert rows[0]["status"] == "queued"
    assert rows[0]["execution_state"] == "LIVE · coinbase · limit"
    assert rows[1]["asset"] == "ETH"
    assert rows[1]["status"] == "executed"
    assert rows[1]["execution_state"] == "SELL 0.25 @ 4,420.00 · paper"


def test_load_local_recommendations_prefers_signal_inbox(monkeypatch) -> None:
    class FakeInbox:
        def list_signals(self, limit: int = 20):
            assert limit == 5
            return [
                {
                    "signal_id": "sig_1",
                    "symbol": "btc/usd",
                    "action": "long",
                    "confidence": 0.82,
                    "notes": "Breakout held above support",
                    "source": "tradingview",
                    "author": "desk",
                    "status": "new",
                },
                {
                    "signal_id": "sig_2",
                    "symbol": "BTCUSDT",
                    "action": "sell",
                    "confidence": 0.41,
                    "notes": "Older duplicate asset signal",
                    "source": "tradingview",
                    "author": "desk",
                    "status": "rejected",
                },
            ]

    class FakeEvidence:
        def recent_signals(self, limit: int = 20):
            raise AssertionError("evidence store should not be used when inbox rows exist")

    monkeypatch.setattr("storage.signal_inbox_sqlite.SignalInboxSQLite", FakeInbox)
    monkeypatch.setattr("storage.evidence_signals_sqlite.EvidenceSignalsSQLite", FakeEvidence)

    rows = view_data._load_local_recommendations(limit=5)
    assert rows == [
        {
            "id": "sig_1",
            "asset": "BTC",
            "signal": "buy",
            "confidence": 0.82,
            "summary": "Breakout held above support",
            "evidence": "tradingview",
            "status": "pending_review",
        }
    ]


def test_load_local_recommendations_falls_back_to_evidence_store(monkeypatch) -> None:
    class FakeInbox:
        def list_signals(self, limit: int = 20):
            return []

    class FakeEvidence:
        def recent_signals(self, limit: int = 20):
            assert limit == 3
            return [
                {
                    "signal_id": "ev_1",
                    "symbol": "ETH-USDT",
                    "side": "short",
                    "confidence": 0.61,
                    "notes": "Funding rolled over",
                    "source_id": "partner_feed",
                    "status": "scored",
                }
            ]

    monkeypatch.setattr("storage.signal_inbox_sqlite.SignalInboxSQLite", FakeInbox)
    monkeypatch.setattr("storage.evidence_signals_sqlite.EvidenceSignalsSQLite", FakeEvidence)

    rows = view_data._load_local_recommendations(limit=3)
    assert rows == [
        {
            "id": "ev_1",
            "asset": "ETH",
            "signal": "sell",
            "confidence": 0.61,
            "summary": "Funding rolled over",
            "evidence": "partner_feed",
            "status": "pending_review",
        }
    ]


def test_recent_activity_prefers_audit_details(monkeypatch) -> None:
    payload = {
        "status": "success",
        "data": {
            "items": [
                {"action": "explain_asset", "details": "Generated explanation for SOL"},
                {"action": "evaluate_trade", "details": "Execution disabled in research mode"},
            ]
        },
    }
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: payload if path == "/api/v1/audit/events" else None,
    )
    monkeypatch.setattr(view_data, "_load_local_recent_activity", lambda limit=6: [])
    rows = view_data.get_recent_activity()
    assert rows == ["Generated explanation for SOL", "Execution disabled in research mode"]


def test_recent_activity_prefers_local_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_load_local_recent_activity",
        lambda limit=6: ["Health check passed", "Listing logs refreshed"],
    )
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda path: None)

    rows = view_data.get_recent_activity()
    assert rows == ["Health check passed", "Listing logs refreshed"]


def test_load_local_recent_activity_prefers_ops_events(monkeypatch) -> None:
    class FakeOpsEventStore:
        def __init__(self, exec_db: str):
            assert exec_db == "/tmp/test-exec.sqlite"

        def list_recent(self, limit: int = 100):
            assert limit == 4
            return [
                {"message": "Health check passed", "event_type": "health_check"},
                {"message": "Listing logs refreshed", "event_type": "listing_logs"},
                {"message": "Health check passed", "event_type": "health_check"},
            ]

    def _unexpected_intent_events(limit=200):
        raise AssertionError("intent audit should not be used")

    class FakeDecisionAuditStore:
        def last_decisions(self, limit: int = 200):
            raise AssertionError("decision audit should not be used")

    monkeypatch.setattr(view_data, "_resolve_execution_db_path", lambda: "/tmp/test-exec.sqlite")
    monkeypatch.setattr("storage.ops_event_store_sqlite.OpsEventStore", FakeOpsEventStore)
    monkeypatch.setattr("services.execution.intent_audit.recent_intent_events", _unexpected_intent_events)
    monkeypatch.setattr("storage.decision_audit_store_sqlite.DecisionAuditStoreSQLite", FakeDecisionAuditStore)

    rows = view_data._load_local_recent_activity(limit=4)
    assert rows == ["Health check passed", "Listing logs refreshed"]


def test_load_local_recent_activity_falls_back_to_intent_audit(monkeypatch) -> None:
    class FakeOpsEventStore:
        def __init__(self, exec_db: str):
            pass

        def list_recent(self, limit: int = 100):
            return []

    monkeypatch.setattr(view_data, "_resolve_execution_db_path", lambda: "/tmp/test-exec.sqlite")
    monkeypatch.setattr("storage.ops_event_store_sqlite.OpsEventStore", FakeOpsEventStore)
    monkeypatch.setattr(
        "services.execution.intent_audit.recent_intent_events",
        lambda limit=200: [
            {
                "symbol": "sol/usd",
                "status": "accepted",
                "summary": "submit:accepted",
                "payload": {"event": "submit", "status": "accepted"},
            }
        ],
    )

    rows = view_data._load_local_recent_activity(limit=3)
    assert rows == ["Submit · SOL · accepted"]


def test_portfolio_view_uses_dashboard_watchlist_marks(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_load_local_portfolio_snapshot", lambda _prices: None)
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "portfolio": {
                "total_value": 1000.0,
                "cash": 300.0,
                "unrealized_pnl": 25.0,
                "exposure_used_pct": 17.5,
            },
            "watchlist": [
                {"asset": "BTC", "price": 90000.0},
                {"asset": "SOL", "price": 200.0},
            ],
        },
    )

    payload = view_data.get_portfolio_view()
    assert payload["portfolio"]["cash"] == 300.0
    assert payload["positions"][0]["asset"] == "BTC"
    assert payload["positions"][0]["mark"] == 90000.0
    assert payload["positions"][1]["mark"] == 200.0


def test_portfolio_view_prefers_local_portfolio_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "portfolio": {
                "total_value": 1000.0,
                "cash": 300.0,
                "unrealized_pnl": 25.0,
                "exposure_used_pct": 17.5,
            },
            "watchlist": [{"asset": "BTC", "price": 90000.0}],
        },
    )
    monkeypatch.setattr(
        view_data,
        "_load_local_portfolio_snapshot",
        lambda _prices: {
            "portfolio": {
                "total_value": 1500.0,
                "cash": 450.0,
                "unrealized_pnl": 120.0,
                "realized_pnl_24h": 35.0,
                "exposure_used_pct": 28.5,
                "leverage": 1.0,
            },
            "positions": [
                {
                    "asset": "BTC",
                    "symbol": "BTC/USD",
                    "venue": "paper",
                    "side": "long",
                    "size": 0.02,
                    "entry": 85000.0,
                    "mark": 90000.0,
                    "pnl": 100.0,
                }
            ],
        },
    )

    payload = view_data.get_portfolio_view()
    assert payload["portfolio"]["total_value"] == 1500.0
    assert payload["portfolio"]["cash"] == 450.0
    assert payload["positions"][0]["venue"] == "paper"
    assert payload["positions"][0]["asset"] == "BTC"


def test_markets_view_prefers_requested_asset_and_related_signal(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_load_current_regime", lambda: "trend_up")
    monkeypatch.setattr(
        view_data,
        "_load_signal_reliability",
        lambda asset: {"hit_rate": 0.68, "n_scored": 84, "avg_return_bps": 160.0} if asset == "SOL" else None,
    )
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5, "signal": "research"},
            ]
        },
    )
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {
                "asset": "SOL",
                "signal": "buy",
                "confidence": 0.81,
                "summary": "Momentum with catalyst support",
                "evidence": "volume expansion",
                "status": "pending_review",
            }
        ],
    )
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "Momentum with catalyst support",
            "past_precedent": "Prior momentum cycles showed similar behavior",
            "future_catalyst": "A governance milestone remains in focus",
            "confidence": 0.81,
            "risk_note": "Research only.",
            "execution_disabled": True,
            "evidence": [
                {
                    "type": "market",
                    "source": "coinbase",
                    "summary": "volume expansion",
                    "timestamp": "2026-03-11T12:55:00Z",
                    "relevance": 0.93,
                }
            ],
        },
    )
    monkeypatch.setattr(view_data, "_load_local_market_snapshot", lambda venue, symbol, asset: None)
    monkeypatch.setattr(view_data, "_load_local_ohlcv", lambda venue, symbol, timeframe="1h", limit=24: [])

    payload = view_data.get_markets_view(selected_asset="SOL")
    assert payload["selected_asset"] == "SOL"
    assert payload["detail"]["asset"] == "SOL"
    assert payload["detail"]["confidence"] == 0.81
    assert payload["detail"]["market_bias"] == "bullish"
    assert payload["detail"]["price_series"][-1] == 200.0
    assert payload["detail"]["current_cause"] == "Momentum with catalyst support"
    assert payload["detail"]["evidence_items"][0]["summary"] == "volume expansion"
    assert payload["detail"]["related_signals"][0]["status"] == "pending_review"
    assert payload["detail"]["regime"] == "trend_up"
    assert payload["detail"]["category"] in {"top_opportunity", "watch_closely"}
    assert payload["detail"]["opportunity_score"] > 0.0
    assert payload["watchlist"][1]["regime"] == "trend_up"
    assert payload["watchlist"][1]["category"] in {"top_opportunity", "watch_closely"}
    assert payload["detail"]["related_signals"][0]["category"] in {"top_opportunity", "watch_closely"}


def test_markets_view_defaults_to_research_asset(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
                {"asset": "ETH", "price": 4100.0, "change_24h_pct": 0.7, "signal": "monitor"},
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5, "signal": "research"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "",
            "past_precedent": "",
            "future_catalyst": "",
            "confidence": 0.0,
            "risk_note": "",
            "execution_disabled": True,
            "evidence": [],
        },
    )
    monkeypatch.setattr(view_data, "_load_local_market_snapshot", lambda venue, symbol, asset: None)
    monkeypatch.setattr(view_data, "_load_local_ohlcv", lambda venue, symbol, timeframe="1h", limit=24: [])

    payload = view_data.get_markets_view()
    assert payload["selected_asset"] == "SOL"
    assert payload["detail"]["asset"] == "SOL"
    assert payload["detail"]["related_signals"][0]["summary"].startswith("No direct recommendation")
    assert payload["detail"]["question"] == "Why is SOL moving?"


def test_signals_view_prefers_pending_review_signal(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_load_current_regime", lambda: "trend_up")
    monkeypatch.setattr(view_data, "_load_signal_reliability", lambda asset: {"hit_rate": 0.7, "n_scored": 50, "avg_return_bps": 120.0})
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {
                "asset": "BTC",
                "signal": "hold",
                "confidence": 0.66,
                "summary": "Range breakout not confirmed",
                "status": "watch",
                "execution_state": "",
                "evidence": "weak continuation volume",
            },
            {
                "asset": "SOL",
                "signal": "buy",
                "confidence": 0.81,
                "summary": "Momentum with catalyst support",
                "status": "pending_review",
                "execution_state": "LIVE · coinbase · limit",
                "evidence": "volume expansion",
            },
        ],
    )
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8},
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5},
            ]
        },
    )
    monkeypatch.setattr(
        view_data,
        "get_markets_view",
        lambda selected_asset=None: {
            "detail": {
                "asset": selected_asset or "SOL",
                "current_cause": "Momentum with catalyst support",
                "price": 200.0,
                "change_24h_pct": 6.5,
                "signal": "buy",
                "status": "pending_review",
                "execution_state": "LIVE · coinbase · limit",
                "confidence": 0.81,
                "execution_disabled": True,
                "risk_note": "Research only.",
                "price_series": [190.0, 195.0, 200.0],
                "evidence_items": [{"summary": "volume expansion"}],
            }
        },
    )

    payload = view_data.get_signals_view()
    assert payload["selected_asset"] == "SOL"
    assert payload["signals"][0]["asset"] == "BTC"
    assert payload["signals"][1]["price"] == 200.0
    assert payload["signals"][1]["execution_state"] == "LIVE · coinbase · limit"
    assert payload["signals"][1]["regime"] == "trend_up"
    assert payload["signals"][1]["category"] in {"top_opportunity", "watch_closely"}
    assert payload["signals"][1]["opportunity_score"] > 0.0
    assert payload["detail"]["asset"] == "SOL"
    assert payload["detail"]["execution_state"] == "LIVE · coinbase · limit"
    assert payload["detail"]["current_cause"] == "Momentum with catalyst support"
    assert payload["detail"]["regime"] == "trend_up"
    assert payload["detail"]["opportunity_score"] == payload["signals"][1]["opportunity_score"]


def test_signals_view_respects_requested_asset(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_load_current_regime", lambda: "event_driven")
    monkeypatch.setattr(view_data, "_load_signal_reliability", lambda asset: None)
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {"asset": "BTC", "signal": "hold", "confidence": 0.66, "summary": "Range trade", "status": "watch", "evidence": "volume"},
            {"asset": "SOL", "signal": "buy", "confidence": 0.81, "summary": "Momentum", "status": "pending_review", "evidence": "catalyst"},
        ],
    )
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"watchlist": []})
    monkeypatch.setattr(
        view_data,
        "get_markets_view",
        lambda selected_asset=None: {"detail": {"asset": selected_asset or "BTC"}},
    )

    payload = view_data.get_signals_view(selected_asset="BTC")
    assert payload["selected_asset"] == "BTC"
    assert payload["detail"]["asset"] == "BTC"
    assert payload["signals"][0]["regime"] == "event_driven"
    assert payload["signals"][0]["category"]


def test_overview_view_reuses_signals_detail_contract(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"mode": "research_only", "portfolio": {"total_value": 1000.0}})
    monkeypatch.setattr(view_data, "get_recent_activity", lambda: ["Generated explanation for SOL"])
    monkeypatch.setattr(
        view_data,
        "get_signals_view",
        lambda selected_asset=None: {
            "selected_asset": selected_asset or "SOL",
            "signals": [
                {
                    "asset": "SOL",
                    "signal": "buy",
                    "confidence": 0.81,
                    "status": "pending_review",
                    "execution_state": "LIVE · coinbase · limit",
                    "summary": "Momentum with catalyst support",
                    "regime": "trend_up",
                    "category": "top_opportunity",
                    "opportunity_score": 0.74,
                }
            ],
            "detail": {
                "asset": selected_asset or "SOL",
                "current_cause": "Momentum with catalyst support",
                "execution_state": "LIVE · coinbase · limit",
                "future_catalyst": "A governance milestone remains in focus",
            },
        },
    )

    payload = view_data.get_overview_view()
    assert payload["summary"]["mode"] == "research_only"
    assert payload["selected_asset"] == "SOL"
    assert payload["signals"][0]["thesis"] == "Momentum with catalyst support"
    assert payload["signals"][0]["execution_state"] == "LIVE · coinbase · limit"
    assert payload["signals"][0]["regime"] == "trend_up"
    assert payload["signals"][0]["category"] == "top_opportunity"
    assert payload["signals"][0]["opportunity_score"] == 0.74
    assert payload["detail"]["future_catalyst"] == "A governance milestone remains in focus"
    assert payload["recent_activity"] == ["Generated explanation for SOL"]


def test_overview_view_includes_ranked_watchlist_preview(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "mode": "research_only",
            "portfolio": {"total_value": 1000.0},
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 2.1, "signal": "watch", "snapshot_source": "api"},
                {"asset": "ETH", "price": 4100.0, "change_24h_pct": -4.8, "signal": "monitor", "snapshot_source": "local_ws"},
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5, "signal": "research", "snapshot_source": "api"},
                {"asset": "LINK", "price": 18.5, "change_24h_pct": 1.1, "signal": "watch"},
                {"asset": "AVAX", "price": 54.2, "change_24h_pct": -3.4, "signal": "monitor"},
                {"asset": "DOGE", "price": 0.31, "change_24h_pct": 0.6, "signal": "watch"},
            ],
        },
    )
    monkeypatch.setattr(view_data, "get_recent_activity", lambda: ["Generated explanation for SOL"])
    monkeypatch.setattr(
        view_data,
        "get_signals_view",
        lambda selected_asset=None: {
            "selected_asset": selected_asset or "SOL",
            "signals": [],
            "detail": {"asset": selected_asset or "SOL"},
        },
    )

    payload = view_data.get_overview_view()
    assert [row["asset"] for row in payload["watchlist_preview"]] == ["SOL", "ETH", "AVAX", "BTC", "LINK"]
    assert payload["watchlist_preview"][0]["source"] == "api"
    assert payload["watchlist_preview"][1]["source"] == "local_ws"
    assert payload["watchlist_preview"][-1]["change_24h_pct"] == 1.1


def test_research_explain_uses_api_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_request_envelope",
        lambda path, method="GET", payload=None: {
            "status": "success",
            "data": {
                "asset": "BTC",
                "question": "Why is BTC moving?",
                "current_cause": "Spot demand improved.",
                "past_precedent": "Breakout history is constructive.",
                "future_catalyst": "Macro events remain pending.",
                "confidence": 0.74,
                "risk_note": "Research only.",
                "execution_disabled": True,
                "evidence": [{"type": "market", "source": "coinbase", "summary": "bid support", "relevance": 0.82}],
            },
        }
        if path == "/api/v1/research/explain" and method == "POST"
        else None,
    )

    payload = view_data.get_research_explain("BTC")
    assert payload["asset"] == "BTC"
    assert payload["current_cause"] == "Spot demand improved."
    assert payload["confidence"] == 0.74
    assert payload["assistant_status"] == {
        "provider": "backend_api",
        "model": None,
        "fallback": False,
        "message": None,
    }


def test_research_explain_falls_back_to_phase1_orchestrator(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)
    monkeypatch.setattr(
        view_data,
        "_request_envelope_from_base",
        lambda base_url, path, method="GET", payload=None: {
            "ok": True,
            "asset": "BTC",
            "question": "Why is BTC moving?",
            "current_cause": "BTC is firming on spot demand.",
            "past_precedent": "Prior breakouts held when liquidity stayed firm.",
            "future_catalyst": "Macro data later this week could matter.",
            "confidence": 0.72,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [{"type": "market", "source": "coinbase", "summary": "spot support", "relevance": 0.8}],
            "assistant_status": {"provider": "openai", "fallback": False},
        }
        if base_url == view_data.PHASE1_ORCHESTRATOR_URL and path == "/v1/explain" and method == "POST"
        else None,
    )

    payload = view_data.get_research_explain("BTC")
    assert payload["asset"] == "BTC"
    assert payload["current_cause"] == "BTC is firming on spot demand."
    assert payload["assistant_status"]["provider"] == "openai"
    assert payload["assistant_status"]["fallback"] is False


def test_markets_view_prefers_candle_api_series(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "Spot demand improved.",
            "past_precedent": "",
            "future_catalyst": "",
            "confidence": 0.74,
            "risk_note": "Research only.",
            "execution_disabled": True,
            "evidence": [],
        },
    )
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: {
            "status": "success",
            "data": {
                "candles": [
                    {"close": 88100.0},
                    {"close": 89450.5},
                    {"close": 90010.25},
                ]
            },
        }
        if path == "/api/v1/market/BTC/candles?exchange=coinbase&interval=1h&limit=24"
        else None,
    )
    monkeypatch.setattr(view_data, "_load_local_market_snapshot", lambda venue, symbol, asset: None)
    monkeypatch.setattr(
        view_data,
        "_load_local_ohlcv",
        lambda venue, symbol, timeframe="1h", limit=24: [[0, 0, 0, 0, 1.0, 0.0]],
    )

    payload = view_data.get_markets_view(selected_asset="BTC")
    assert payload["detail"]["price_series"] == [88100.0, 89450.5, 90010.25]


def test_markets_view_falls_back_to_local_ohlcv_series(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "Spot demand improved.",
            "past_precedent": "",
            "future_catalyst": "",
            "confidence": 0.74,
            "risk_note": "Research only.",
            "execution_disabled": True,
            "evidence": [],
        },
    )
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda path: None)
    monkeypatch.setattr(view_data, "_load_local_market_snapshot", lambda venue, symbol, asset: None)

    seen: dict[str, object] = {}

    def _fake_load(venue, symbol, timeframe="1h", limit=24):
        seen["venue"] = venue
        seen["symbol"] = symbol
        seen["timeframe"] = timeframe
        seen["limit"] = limit
        return [
            [1, 0.0, 0.0, 0.0, 88100.0, 0.0],
            [2, 0.0, 0.0, 0.0, 89450.5, 0.0],
            [3, 0.0, 0.0, 0.0, 90010.25, 0.0],
        ]

    monkeypatch.setattr(view_data, "_load_local_ohlcv", _fake_load)

    payload = view_data.get_markets_view(selected_asset="BTC")
    assert payload["detail"]["price_series"] == [88100.0, 89450.5, 90010.25]
    assert seen == {"venue": "coinbase", "symbol": "BTC/USD", "timeframe": "1h", "limit": 24}


def test_markets_view_falls_back_to_synthetic_series_when_history_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5, "signal": "research"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "Momentum with catalyst support",
            "past_precedent": "",
            "future_catalyst": "",
            "confidence": 0.81,
            "risk_note": "Research only.",
            "execution_disabled": True,
            "evidence": [],
        },
    )
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda path: None)
    monkeypatch.setattr(view_data, "_load_local_market_snapshot", lambda venue, symbol, asset: None)
    monkeypatch.setattr(view_data, "_load_local_ohlcv", lambda venue, symbol, timeframe="1h", limit=24: [])

    payload = view_data.get_markets_view(selected_asset="SOL")
    assert payload["detail"]["price_series"]
    assert payload["detail"]["price_series"][-1] == 200.0


def test_markets_view_prefers_market_snapshot_api_for_detail_price(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "Spot demand improved.",
            "past_precedent": "",
            "future_catalyst": "",
            "confidence": 0.74,
            "risk_note": "Research only.",
            "execution_disabled": True,
            "evidence": [],
        },
    )
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: {
            "status": "success",
            "data": {
                "asset": "BTC",
                "exchange": "coinbase",
                "last_price": 90555.25,
                "bid": 90550.0,
                "ask": 90560.5,
                "spread": 10.5,
                "volume_24h": 125000000.0,
                "timestamp": "2026-03-11T12:55:00Z",
            },
        }
        if path == "/api/v1/market/BTC/snapshot?exchange=coinbase"
        else None,
    )
    monkeypatch.setattr(view_data, "_load_local_market_snapshot", lambda venue, symbol, asset: None)
    monkeypatch.setattr(view_data, "_load_local_ohlcv", lambda venue, symbol, timeframe="1h", limit=24: [])

    payload = view_data.get_markets_view(selected_asset="BTC")
    assert payload["detail"]["price"] == 90555.25
    assert payload["detail"]["support"] == 89196.92
    assert payload["detail"]["resistance"] == 91913.58
    assert payload["detail"]["bid"] == 90550.0
    assert payload["detail"]["ask"] == 90560.5
    assert payload["detail"]["spread"] == 10.5
    assert payload["detail"]["snapshot_source"] == "api"


def test_markets_view_falls_back_to_local_snapshot_for_detail_price(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "Spot demand improved.",
            "past_precedent": "",
            "future_catalyst": "",
            "confidence": 0.74,
            "risk_note": "Research only.",
            "execution_disabled": True,
            "evidence": [],
        },
    )
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda path: None)
    monkeypatch.setattr(
        view_data,
        "_load_local_market_snapshot",
        lambda venue, symbol, asset: {
            "asset": asset,
            "exchange": venue,
            "last_price": 90400.0,
            "bid": 90395.0,
            "ask": 90405.0,
            "spread": 10.0,
            "volume_24h": 0.0,
            "timestamp": "200",
            "source": "local_ws",
        },
    )
    monkeypatch.setattr(view_data, "_load_local_ohlcv", lambda venue, symbol, timeframe="1h", limit=24: [])

    payload = view_data.get_markets_view(selected_asset="BTC")
    assert payload["detail"]["price"] == 90400.0
    assert payload["detail"]["support"] == 89044.0
    assert payload["detail"]["resistance"] == 91756.0
    assert payload["detail"]["snapshot_source"] == "local_ws"
    assert payload["detail"]["exchange"] == "coinbase"


def test_research_explain_rejects_foreign_asset_copy(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_request_envelope",
        lambda path, method="GET", payload=None: {
            "status": "success",
            "data": {
                "asset": "BTC",
                "question": "Why is BTC moving?",
                "current_cause": "SOL is rising alongside increased spot volume and fresh ecosystem headlines.",
                "past_precedent": "Similar moves previously followed ecosystem upgrade narratives.",
                "future_catalyst": "A scheduled governance milestone may still matter.",
                "confidence": 0.78,
                "risk_note": "Research only.",
                "execution_disabled": True,
                "evidence": [],
            },
        }
        if path == "/api/v1/research/explain" and method == "POST"
        else None,
    )
    monkeypatch.setattr(
        view_data,
        "_request_envelope_from_base",
        lambda base_url, path, method="GET", payload=None: {
            "ok": True,
            "asset": "BTC",
            "question": "Why is BTC moving?",
            "current_cause": "BTC is firming on spot demand.",
            "past_precedent": "Prior breakouts held when liquidity stayed firm.",
            "future_catalyst": "Macro data later this week could matter.",
            "confidence": 0.72,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [],
            "assistant_status": {"provider": "openai", "fallback": False},
        }
        if base_url == view_data.PHASE1_ORCHESTRATOR_URL and path == "/v1/explain" and method == "POST"
        else None,
    )

    payload = view_data.get_research_explain("BTC")
    assert payload["asset"] == "BTC"
    assert "SOL" not in payload["current_cause"]
    assert payload["current_cause"] == "BTC is firming on spot demand."
    assert payload["assistant_status"]["provider"] == "openai"


def test_research_explain_falls_back_for_non_sol_assets(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)
    monkeypatch.setattr(view_data, "_read_mock_envelope", lambda _name: None)

    payload = view_data.get_research_explain("ADA")
    assert payload["asset"] == "ADA"
    assert payload["question"] == "Why is ADA moving?"
    assert payload["execution_disabled"] is True
    assert len(payload["evidence"]) == 1
    assert payload["assistant_status"] == {
        "provider": "dashboard_fallback",
        "model": None,
        "fallback": True,
        "message": "Static asset-aware dashboard fallback used because no valid explain response was available.",
    }


def test_trades_view_maps_recommendations_to_pending_approvals(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_load_local_pending_approvals", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_open_orders", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_failed_orders", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_recent_fills", lambda limit=20: [])
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {"approval_required": False},
    )
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {
                "id": "rec_99",
                "asset": "SOL",
                "signal": "buy",
                "risk_size_pct": 1.5,
                "status": "pending_review",
            }
        ],
    )

    payload = view_data.get_trades_view()
    assert payload["approval_required"] is False
    assert payload["pending_approvals"][0]["id"] == "rec_99"
    assert payload["pending_approvals"][0]["side"] == "buy"
    assert payload["open_orders"] == []
    assert payload["failed_orders"] == []
    assert len(payload["recent_fills"]) >= 1


def test_trades_view_prefers_local_recent_fills(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"approval_required": True})
    monkeypatch.setattr(view_data, "_load_local_pending_approvals", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_open_orders", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_failed_orders", lambda limit=20: [])
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "_load_local_recent_fills",
        lambda limit=20: [
            {
                "ts": "2026-03-12T00:05:00Z",
                "asset": "ETH",
                "side": "sell",
                "qty": 0.25,
                "price": 4420.0,
                "venue": "paper",
            }
        ],
    )

    payload = view_data.get_trades_view()
    assert payload["approval_required"] is True
    assert payload["recent_fills"] == [
        {
            "ts": "2026-03-12T00:05:00Z",
            "asset": "ETH",
            "side": "sell",
            "qty": 0.25,
            "price": 4420.0,
            "venue": "paper",
        }
    ]
    assert payload["pending_approvals"][0]["asset"] == "SOL"


def test_trades_view_prefers_local_pending_approvals(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"approval_required": True})
    monkeypatch.setattr(
        view_data,
        "_load_local_pending_approvals",
        lambda limit=20: [
            {
                "id": "intent_live_1",
                "asset": "BTC",
                "side": "buy",
                "qty": 0.05,
                "risk_size_pct": 0.0,
                "venue": "coinbase",
                "mode": "live",
                "order_type": "limit",
                "limit_price": 90100.0,
                "status": "queued",
                "created_ts": "2026-03-12T10:05:00Z",
                "source": "signal_router",
            }
        ],
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [{"asset": "SOL", "signal": "buy", "status": "pending_review"}])
    monkeypatch.setattr(view_data, "_load_local_open_orders", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_failed_orders", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_recent_fills", lambda limit=20: [])

    payload = view_data.get_trades_view()
    assert payload["pending_approvals"][0]["id"] == "intent_live_1"
    assert payload["pending_approvals"][0]["mode"] == "live"
    assert payload["pending_approvals"][0]["asset"] == "BTC"


def test_trades_view_prefers_local_open_orders(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"approval_required": True})
    monkeypatch.setattr(view_data, "_load_local_pending_approvals", lambda limit=20: [])
    monkeypatch.setattr(
        view_data,
        "_load_local_open_orders",
        lambda limit=20: [
            {
                "id": "open_live_1",
                "asset": "ETH",
                "side": "buy",
                "qty": 0.75,
                "venue": "coinbase",
                "mode": "live",
                "order_type": "limit",
                "limit_price": 4410.0,
                "status": "working",
                "created_ts": "2026-03-12T10:10:00Z",
                "exchange_order_id": "ex_live_1",
                "source": "live_orders",
            }
        ],
    )
    monkeypatch.setattr(view_data, "_load_local_failed_orders", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_recent_fills", lambda limit=20: [])
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])

    payload = view_data.get_trades_view()
    assert payload["open_orders"][0]["id"] == "open_live_1"
    assert payload["open_orders"][0]["status"] == "working"
    assert payload["pending_approvals"][0]["asset"] == "SOL"


def test_trades_view_prefers_local_failed_orders(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"approval_required": True})
    monkeypatch.setattr(view_data, "_load_local_pending_approvals", lambda limit=20: [])
    monkeypatch.setattr(view_data, "_load_local_open_orders", lambda limit=20: [])
    monkeypatch.setattr(
        view_data,
        "_load_local_failed_orders",
        lambda limit=20: [
            {
                "id": "failed_live_1",
                "asset": "ADA",
                "side": "sell",
                "qty": 200.0,
                "venue": "coinbase",
                "mode": "live",
                "order_type": "limit",
                "limit_price": 1.05,
                "status": "failed",
                "created_ts": "2026-03-12T10:12:00Z",
                "exchange_order_id": "ex_fail_1",
                "reason": "exchange unavailable",
                "source": "live_orders",
            }
        ],
    )
    monkeypatch.setattr(view_data, "_load_local_recent_fills", lambda limit=20: [])
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])

    payload = view_data.get_trades_view()
    assert payload["failed_orders"][0]["id"] == "failed_live_1"
    assert payload["failed_orders"][0]["reason"] == "exchange unavailable"


def test_load_local_pending_approvals_prefers_queued_intents(monkeypatch) -> None:
    class FakePaperQueue:
        def list_intents(self, limit: int = 500, status: str | None = None):
            assert limit == 3
            assert status is None
            return [
                {
                    "intent_id": "paper_1",
                    "created_ts": "2026-03-12T09:00:00Z",
                    "symbol": "sol/usd",
                    "side": "buy",
                    "qty": 4.0,
                    "order_type": "market",
                    "status": "queued",
                    "venue": "paper",
                    "source": "signal_router",
                },
                {
                    "intent_id": "paper_done",
                    "created_ts": "2026-03-12T08:00:00Z",
                    "symbol": "eth/usd",
                    "side": "sell",
                    "qty": 1.0,
                    "order_type": "limit",
                    "limit_price": 4400.0,
                    "status": "filled",
                    "venue": "paper",
                    "source": "signal_router",
                },
            ]

    class FakeLiveQueue:
        def list_intents(self, limit: int = 500, status: str | None = None):
            assert limit == 3
            assert status is None
            return [
                {
                    "intent_id": "live_1",
                    "created_ts": "2026-03-12T10:00:00Z",
                    "symbol": "BTC-USDT",
                    "side": "sell",
                    "qty": 0.1,
                    "order_type": "limit",
                    "limit_price": 90500.0,
                    "status": "held",
                    "venue": "coinbase",
                    "source": "live_executor",
                }
            ]

    monkeypatch.setattr("storage.intent_queue_sqlite.IntentQueueSQLite", FakePaperQueue)
    monkeypatch.setattr("storage.live_intent_queue_sqlite.LiveIntentQueueSQLite", FakeLiveQueue)

    rows = view_data._load_local_pending_approvals(limit=3)
    assert rows == [
        {
            "id": "live_1",
            "asset": "BTC",
            "side": "sell",
            "qty": 0.1,
            "risk_size_pct": 0.0,
            "venue": "coinbase",
            "mode": "live",
            "order_type": "limit",
            "limit_price": 90500.0,
            "status": "held",
            "created_ts": "2026-03-12T10:00:00Z",
            "source": "live_executor",
        },
        {
            "id": "paper_1",
            "asset": "SOL",
            "side": "buy",
            "qty": 4.0,
            "risk_size_pct": 0.0,
            "venue": "paper",
            "mode": "paper",
            "order_type": "market",
            "limit_price": None,
            "status": "queued",
            "created_ts": "2026-03-12T09:00:00Z",
            "source": "signal_router",
        },
    ]


def test_load_local_open_orders_prefers_live_and_paper_orders(monkeypatch) -> None:
    class FakeLiveTrading:
        def list_orders(self, limit: int = 300):
            assert limit == 3
            return [
                {
                    "client_order_id": "live_open_1",
                    "created_ts": "2026-03-12T10:15:00Z",
                    "venue": "coinbase",
                    "symbol": "BTC-USDT",
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 0.05,
                    "limit_price": 90250.0,
                    "exchange_order_id": "cb_1",
                    "status": "open",
                },
                {
                    "client_order_id": "live_done_1",
                    "created_ts": "2026-03-12T08:15:00Z",
                    "venue": "coinbase",
                    "symbol": "ETH-USDT",
                    "side": "sell",
                    "order_type": "market",
                    "qty": 0.5,
                    "limit_price": None,
                    "exchange_order_id": "cb_2",
                    "status": "filled",
                },
            ]

    class FakePaperTrading:
        def list_orders(self, limit: int = 500, status: str | None = None):
            assert limit == 3
            assert status is None
            return [
                {
                    "order_id": "paper_open_1",
                    "client_order_id": "paper_client_1",
                    "created_ts": "2026-03-12T09:30:00Z",
                    "ts": "2026-03-12T09:30:00Z",
                    "venue": "paper",
                    "symbol": "sol/usd",
                    "side": "sell",
                    "order_type": "market",
                    "qty": 4.0,
                    "limit_price": None,
                    "status": "submitted",
                }
            ]

    monkeypatch.setattr("storage.live_trading_sqlite.LiveTradingSQLite", FakeLiveTrading)
    monkeypatch.setattr("storage.paper_trading_sqlite.PaperTradingSQLite", FakePaperTrading)
    monkeypatch.setattr("storage.execution_audit_reader.list_orders", lambda limit=3: [])

    rows = view_data._load_local_open_orders(limit=3)
    assert rows == [
        {
            "id": "live_open_1",
            "asset": "BTC",
            "side": "buy",
            "qty": 0.05,
            "venue": "coinbase",
            "mode": "live",
            "order_type": "limit",
            "limit_price": 90250.0,
            "status": "open",
            "created_ts": "2026-03-12T10:15:00Z",
            "exchange_order_id": "cb_1",
            "source": "live_orders",
        },
        {
            "id": "paper_client_1",
            "asset": "SOL",
            "side": "sell",
            "qty": 4.0,
            "venue": "paper",
            "mode": "paper",
            "order_type": "market",
            "limit_price": None,
            "status": "submitted",
            "created_ts": "2026-03-12T09:30:00Z",
            "exchange_order_id": "",
            "source": "paper_orders",
        },
    ]


def test_load_local_failed_orders_collects_order_and_intent_failures(monkeypatch) -> None:
    class FakeLiveTrading:
        def list_orders(self, limit: int = 300):
            assert limit == 4
            return [
                {
                    "client_order_id": "live_fail_1",
                    "created_ts": "2026-03-12T10:20:00Z",
                    "venue": "coinbase",
                    "symbol": "BTC-USDT",
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 0.05,
                    "limit_price": 90250.0,
                    "exchange_order_id": "cb_fail_1",
                    "status": "error",
                    "last_error": "exchange timeout",
                }
            ]

    class FakePaperTrading:
        def list_orders(self, limit: int = 500, status: str | None = None):
            assert limit == 4
            assert status is None
            return [
                {
                    "order_id": "paper_cancel_1",
                    "client_order_id": "paper_client_cancel_1",
                    "created_ts": "2026-03-12T09:40:00Z",
                    "ts": "2026-03-12T09:40:00Z",
                    "venue": "paper",
                    "symbol": "sol/usd",
                    "side": "sell",
                    "order_type": "market",
                    "qty": 4.0,
                    "limit_price": None,
                    "status": "cancelled",
                    "reject_reason": "user_canceled",
                }
            ]

    class FakeLiveQueue:
        def list_intents(self, limit: int = 500, status: str | None = None):
            assert limit == 4
            assert status is None
            return [
                {
                    "intent_id": "live_intent_fail_1",
                    "updated_ts": "2026-03-12T09:50:00Z",
                    "venue": "coinbase",
                    "symbol": "ETH-USDT",
                    "side": "buy",
                    "order_type": "market",
                    "qty": 0.5,
                    "status": "blocked",
                    "last_error": "risk gate",
                    "exchange_order_id": "",
                }
            ]

    class FakePaperQueue:
        def list_intents(self, limit: int = 500, status: str | None = None):
            assert limit == 4
            assert status is None
            return []

    monkeypatch.setattr("storage.live_trading_sqlite.LiveTradingSQLite", FakeLiveTrading)
    monkeypatch.setattr("storage.paper_trading_sqlite.PaperTradingSQLite", FakePaperTrading)
    monkeypatch.setattr("storage.live_intent_queue_sqlite.LiveIntentQueueSQLite", FakeLiveQueue)
    monkeypatch.setattr("storage.intent_queue_sqlite.IntentQueueSQLite", FakePaperQueue)
    monkeypatch.setattr("storage.execution_audit_reader.list_orders", lambda limit=4: [])

    rows = view_data._load_local_failed_orders(limit=4)
    assert rows == [
        {
            "id": "live_fail_1",
            "asset": "BTC",
            "side": "buy",
            "qty": 0.05,
            "venue": "coinbase",
            "mode": "live",
            "order_type": "limit",
            "limit_price": 90250.0,
            "status": "failed",
            "created_ts": "2026-03-12T10:20:00Z",
            "exchange_order_id": "cb_fail_1",
            "reason": "exchange timeout",
            "source": "live_orders",
        },
        {
            "id": "live_intent_fail_1",
            "asset": "ETH",
            "side": "buy",
            "qty": 0.5,
            "venue": "coinbase",
            "mode": "live",
            "order_type": "market",
            "limit_price": None,
            "status": "rejected",
            "created_ts": "2026-03-12T09:50:00Z",
            "exchange_order_id": "",
            "reason": "risk gate",
            "source": "live_intents",
        },
        {
            "id": "paper_client_cancel_1",
            "asset": "SOL",
            "side": "sell",
            "qty": 4.0,
            "venue": "paper",
            "mode": "paper",
            "order_type": "market",
            "limit_price": None,
            "status": "canceled",
            "created_ts": "2026-03-12T09:40:00Z",
            "exchange_order_id": "",
            "reason": "user_canceled",
            "source": "paper_orders",
        },
    ]


def test_settings_view_uses_api_payload(monkeypatch) -> None:
    payload = {
        "status": "success",
        "data": {
            "general": {"timezone": "UTC", "default_mode": "paper"},
            "notifications": {"telegram": False},
            "ai": {"tone": "concise"},
            "security": {"secret_masking": False},
        },
    }
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: payload if path == "/api/v1/settings" else None,
    )
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})

    settings = view_data.get_settings_view()
    assert settings["general"]["timezone"] == "UTC"
    assert settings["ai"]["tone"] == "concise"


def test_settings_view_applies_local_overlay(monkeypatch) -> None:
    payload = {
        "status": "success",
        "data": {
            "general": {"timezone": "UTC", "default_mode": "paper"},
            "notifications": {"telegram": False},
            "ai": {"tone": "concise"},
            "security": {"secret_masking": False},
        },
    }
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: payload if path == "/api/v1/settings" else None,
    )
    monkeypatch.setattr(
        view_data,
        "load_user_yaml",
        lambda: {
            "symbols": ["BTC/USD", "SOL/USDT"],
            "dashboard_ui": {
                "automation": {"default_mode": "live_auto"},
                "settings": {
                    "general": {"timezone": "America/New_York"},
                    "notifications": {"telegram": True},
                    "ai": {"tone": "detailed"},
                    "security": {"secret_masking": True},
                },
            },
        },
    )

    settings = view_data.get_settings_view()
    assert settings["general"]["timezone"] == "America/New_York"
    assert settings["general"]["default_mode"] == "paper"
    assert settings["general"]["watchlist_defaults"] == ["BTC", "SOL"]
    assert settings["notifications"]["telegram"] is True
    assert settings["ai"]["tone"] == "detailed"
    assert settings["security"]["secret_masking"] is True
    assert settings["notifications"]["email_enabled"] is False
    assert settings["autopilot"]["default_market_universe"] == "core_watchlist"


def test_automation_view_uses_settings_and_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {"execution_enabled": True, "approval_required": False, "mode": "paper"},
    )
    monkeypatch.setattr(
        view_data,
        "get_settings_view",
        lambda: {"general": {"default_mode": "live_approval"}},
    )

    payload = view_data.get_automation_view()
    assert payload["execution_enabled"] is True
    assert payload["dry_run_mode"] is False
    assert payload["default_mode"] == "live_approval"
    assert payload["approval_required_for_live"] is False


def test_update_settings_view_reports_success(monkeypatch) -> None:
    saved_cfg: dict[str, object] = {}

    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(
        view_data,
        "save_user_yaml",
        lambda cfg, dry_run=False: (saved_cfg.update(cfg) or True, "Saved"),
    )
    monkeypatch.setattr(
        view_data,
        "_request_envelope",
        lambda path, method="GET", payload=None: {"status": "success", "data": payload}
        if path == "/api/v1/settings" and method == "PUT"
        else None,
    )

    payload = {"general": {"timezone": "UTC"}}
    result = view_data.update_settings_view(payload)
    assert result["ok"] is True
    assert result["data"] == payload
    assert saved_cfg["dashboard_ui"]["settings"]["general"]["timezone"] == "UTC"


def test_update_settings_view_reports_api_failure(monkeypatch) -> None:
    saved_cfg: dict[str, object] = {}

    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(
        view_data,
        "save_user_yaml",
        lambda cfg, dry_run=False: (saved_cfg.update(cfg) or True, "Saved"),
    )
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)

    result = view_data.update_settings_view({"general": {"timezone": "UTC"}})
    assert result["ok"] is True
    assert "sync skipped" in result["message"].lower()
    assert saved_cfg["dashboard_ui"]["settings"]["general"]["timezone"] == "UTC"


def test_update_settings_view_reports_local_save_failure(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(view_data, "save_user_yaml", lambda cfg, dry_run=False: (False, "disk error"))
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)

    result = view_data.update_settings_view({"general": {"timezone": "UTC"}})
    assert result["ok"] is False
    assert "disk error" in result["message"].lower()


def test_get_automation_view_prefers_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "load_user_yaml",
        lambda: {
            "execution": {
                "executor_mode": "live",
                "live_enabled": False,
                "executor_poll_sec": 3.0,
                "executor_max_per_cycle": 25,
                "paper_fee_bps": 9.0,
                "paper_slippage_bps": 4.0,
                "require_keys_for_live": False,
            },
            "signals": {
                "auto_route_to_paper": True,
                "default_venue": "gateio",
                "default_qty": 0.25,
                "order_type": "limit",
            },
            "dashboard_ui": {
                "automation": {
                    "enabled": True,
                    "dry_run_mode": False,
                    "default_mode": "live_approval",
                    "schedule": "hourly",
                    "marketplace_routing": "approval gated",
                    "approval_required_for_live": True,
                }
            },
        },
    )
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"execution_enabled": False, "approval_required": False})
    monkeypatch.setattr(view_data, "get_settings_view", lambda: {"general": {"default_mode": "paper"}})
    monkeypatch.setattr(
        view_data,
        "_load_automation_operations_snapshot",
        lambda: {"tracked_services": 4, "healthy_services": 3, "attention_services": 1},
    )

    payload = view_data.get_automation_view()
    assert payload["execution_enabled"] is True
    assert payload["default_mode"] == "live_approval"
    assert payload["schedule"] == "hourly"
    assert payload["marketplace_routing"] == "approval gated"
    assert payload["executor_poll_sec"] == 3.0
    assert payload["executor_max_per_cycle"] == 25
    assert payload["paper_fee_bps"] == 9.0
    assert payload["paper_slippage_bps"] == 4.0
    assert payload["require_keys_for_live"] is False
    assert payload["default_venue"] == "gateio"
    assert payload["default_qty"] == 0.25
    assert payload["order_type"] == "limit"
    assert payload["operations_snapshot"] == {
        "tracked_services": 4,
        "healthy_services": 3,
        "attention_services": 1,
    }


def test_update_automation_view_persists_runtime_and_settings(monkeypatch) -> None:
    saved_cfg: dict[str, object] = {}

    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})

    def _fake_save(cfg, dry_run=False):
        saved_cfg.update(cfg)
        return True, "Saved"

    monkeypatch.setattr(view_data, "save_user_yaml", _fake_save)
    monkeypatch.setattr(view_data, "update_settings_view", lambda payload: {"ok": True, "data": payload})

    result = view_data.update_automation_view(
        {
            "execution_enabled": True,
            "dry_run_mode": False,
            "default_mode": "live_auto",
            "schedule": "every 15 min",
            "marketplace_routing": "paper only",
            "approval_required_for_live": False,
            "executor_poll_sec": 2.5,
            "executor_max_per_cycle": 42,
            "paper_fee_bps": 11.0,
            "paper_slippage_bps": 6.5,
            "require_keys_for_live": False,
            "default_venue": "gateio",
            "default_qty": 0.5,
            "order_type": "limit",
        }
    )

    assert result["ok"] is True
    execution = saved_cfg["execution"]
    assert execution["executor_mode"] == "live"
    assert execution["live_enabled"] is True
    assert execution["executor_poll_sec"] == 2.5
    assert execution["executor_max_per_cycle"] == 42
    assert execution["paper_fee_bps"] == 11.0
    assert execution["paper_slippage_bps"] == 6.5
    assert execution["require_keys_for_live"] is False
    assert saved_cfg["signals"]["auto_route_to_paper"] is True
    assert saved_cfg["signals"]["default_venue"] == "gateio"
    assert saved_cfg["signals"]["default_qty"] == 0.5
    assert saved_cfg["signals"]["order_type"] == "limit"
    assert saved_cfg["dashboard_ui"]["automation"]["schedule"] == "every 15 min"


def test_update_automation_view_allows_partial_success(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(view_data, "save_user_yaml", lambda cfg, dry_run=False: (True, "Saved"))
    monkeypatch.setattr(view_data, "update_settings_view", lambda payload: {"ok": False, "message": "api down"})

    result = view_data.update_automation_view(
        {
            "execution_enabled": False,
            "dry_run_mode": True,
            "default_mode": "research_only",
            "schedule": "manual",
            "marketplace_routing": "disabled",
            "approval_required_for_live": True,
        }
    )
    assert result["ok"] is True
    assert "sync skipped" in result["message"].lower()
