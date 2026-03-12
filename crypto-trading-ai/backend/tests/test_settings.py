from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_get_settings() -> None:
    response = client.get("/api/v1/settings")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["general"]["default_mode"] == "research_only"
    assert payload["data"]["security"]["secret_masking"] is True


def test_put_settings() -> None:
    body = {
        "general": {
            "timezone": "America/New_York",
            "default_currency": "USD",
            "startup_page": "/dashboard",
            "default_mode": "research_only",
            "watchlist_defaults": ["BTC", "ETH", "SOL"],
        },
        "notifications": {
            "email": False,
            "telegram": True,
            "discord": False,
            "webhook": False,
            "price_alerts": True,
            "news_alerts": True,
            "catalyst_alerts": True,
            "risk_alerts": True,
            "approval_requests": True,
        },
        "ai": {
            "explanation_length": "normal",
            "tone": "balanced",
            "show_evidence": True,
            "show_confidence": True,
            "include_archives": True,
            "include_onchain": True,
            "include_social": False,
            "allow_hypotheses": True,
        },
        "security": {
            "session_timeout_minutes": 60,
            "secret_masking": True,
            "audit_export_allowed": True,
        },
    }

    response = client.put("/api/v1/settings", json=body)
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["general"]["timezone"] == "America/New_York"
    assert payload["data"]["ai"]["tone"] == "balanced"


def test_patch_settings_partial_update() -> None:
    response = client.put(
        "/api/v1/settings",
        json={
            "general": {
                "startup_page": "/research",
            }
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["general"]["startup_page"] == "/research"
    # Existing values remain when omitted from a partial update.
    assert payload["data"]["general"]["default_currency"] == "USD"


def test_put_settings_empty_update_blocked() -> None:
    response = client.put("/api/v1/settings", json={})
    assert response.status_code == 400
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "EMPTY_SETTINGS_UPDATE"
