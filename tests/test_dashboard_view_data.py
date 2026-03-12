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
