from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
client.headers.update({"Authorization": "Bearer test-viewer-token"})


def test_dashboard_summary() -> None:
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["mode"] == "research_only"
    assert payload["data"]["risk_status"] == "safe"
    assert "portfolio" in payload["data"]
    assert payload["error"] is None
    assert "request_id" in payload
