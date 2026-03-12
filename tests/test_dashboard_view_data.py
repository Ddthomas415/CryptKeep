from __future__ import annotations

from dashboard.services import view_data


def test_dashboard_summary_uses_defaults_when_sources_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda _path: None)
    monkeypatch.setattr(view_data, "_read_mock_envelope", lambda _name: None)

    summary = view_data.get_dashboard_summary()
    assert summary["mode"] == "research_only"
    assert summary["risk_status"] == "safe"
    assert float(summary["portfolio"]["total_value"]) > 0


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
    rows = view_data.get_recommendations()
    assert rows[0]["asset"] == "SOL"
    assert rows[0]["signal"] == "buy"
    assert rows[0]["status"] == "pending_review"


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
    rows = view_data.get_recent_activity()
    assert rows == ["Generated explanation for SOL", "Execution disabled in research mode"]


def test_portfolio_view_uses_dashboard_watchlist_marks(monkeypatch) -> None:
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


def test_trades_view_maps_recommendations_to_pending_approvals(monkeypatch) -> None:
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
    assert len(payload["recent_fills"]) >= 1


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

    settings = view_data.get_settings_view()
    assert settings["general"]["timezone"] == "UTC"
    assert settings["ai"]["tone"] == "concise"


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


def test_update_settings_view_reports_api_failure(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)

    result = view_data.update_settings_view({"general": {"timezone": "UTC"}})
    assert result["ok"] is False
    assert "unavailable" in result["message"].lower()
