from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_terminal_execute_status_allowed() -> None:
    response = client.post("/api/v1/terminal/execute", json={"command": "status"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["requires_confirmation"] is False
    assert payload["data"]["output"][0]["type"] == "text"
    assert "status" in payload["data"]["output"][0]["value"].lower()


def test_terminal_execute_kill_switch_requires_confirmation() -> None:
    response = client.post("/api/v1/terminal/execute", json={"command": "kill-switch on"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["requires_confirmation"] is True
    assert payload["data"]["confirmation_token"]
    assert payload["data"]["output"][0]["type"] == "warning"


def test_terminal_execute_rejects_non_approved_command() -> None:
    response = client.post("/api/v1/terminal/execute", json={"command": "rm -rf /"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["requires_confirmation"] is False
    assert payload["data"]["output"][0]["type"] == "error"
    assert "approved product terminal commands" in payload["data"]["output"][0]["value"].lower()

