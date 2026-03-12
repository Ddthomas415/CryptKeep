from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_trading_recommendations_contract() -> None:
    response = client.get("/api/v1/trading/recommendations")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["error"] is None
    assert isinstance(payload["data"]["items"], list)
    assert len(payload["data"]["items"]) >= 1

    first = payload["data"]["items"][0]
    assert first["side"] in {"buy", "sell"}
    assert first["status"] in {"draft", "pending_review", "approved", "rejected", "expired"}
    assert isinstance(first["mode_compatibility"], list)
    assert all(
        mode in {"research_only", "paper", "live_approval", "live_auto"}
        for mode in first["mode_compatibility"]
    )
    assert isinstance(first["confidence"], float)
    assert 0 <= first["confidence"] <= 1
