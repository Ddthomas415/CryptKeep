from fastapi.testclient import TestClient

from backend.app.main import app

viewer_client = TestClient(app)
viewer_client.headers.update({"Authorization": "Bearer test-viewer-token"})
owner_client = TestClient(app)
owner_client.headers.update({"Authorization": "Bearer test-owner-token"})


def test_risk_summary() -> None:
    response = viewer_client.get("/api/v1/risk/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["risk_status"] == "safe"


def test_risk_limits_get_and_update() -> None:
    get_response = owner_client.get("/api/v1/risk/limits")
    assert get_response.status_code == 200
    before_payload = get_response.json()
    assert before_payload["status"] == "success"
    assert "max_position_size_pct" in before_payload["data"]

    put_response = owner_client.put(
        "/api/v1/risk/limits",
        json={"max_position_size_pct": 2.5},
    )
    assert put_response.status_code == 200
    after_payload = put_response.json()
    assert after_payload["status"] == "success"
    assert after_payload["data"]["max_position_size_pct"] == 2.5


def test_risk_limits_empty_update_blocked() -> None:
    response = owner_client.put("/api/v1/risk/limits", json={})
    assert response.status_code == 400
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "EMPTY_RISK_LIMITS_UPDATE"


def test_risk_limits_require_owner_role() -> None:
    response = viewer_client.get("/api/v1/risk/limits")
    assert response.status_code == 403
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "FORBIDDEN"
