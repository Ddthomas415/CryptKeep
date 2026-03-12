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


def test_terminal_confirm_rejects_invalid_token() -> None:
    response = client.post(
        "/api/v1/terminal/confirm",
        json={"confirmation_token": "confirm_invalid_token"},
    )
    assert response.status_code == 400

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "INVALID_CONFIRMATION_TOKEN"


def test_terminal_confirm_token_is_single_use() -> None:
    execute_response = client.post("/api/v1/terminal/execute", json={"command": "kill-switch on"})
    assert execute_response.status_code == 200
    execute_payload = execute_response.json()
    token = execute_payload["data"]["confirmation_token"]

    confirm_response = client.post("/api/v1/terminal/confirm", json={"confirmation_token": token})
    assert confirm_response.status_code == 200
    confirm_payload = confirm_response.json()
    assert confirm_payload["status"] == "success"
    assert confirm_payload["data"]["confirmed"] is True

    confirm_again_response = client.post("/api/v1/terminal/confirm", json={"confirmation_token": token})
    assert confirm_again_response.status_code == 400
    confirm_again_payload = confirm_again_response.json()
    assert confirm_again_payload["status"] == "error"
    assert confirm_again_payload["error"]["code"] == "INVALID_CONFIRMATION_TOKEN"


def test_terminal_execute_rejects_non_approved_command() -> None:
    response = client.post("/api/v1/terminal/execute", json={"command": "rm -rf /"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["requires_confirmation"] is False
    assert payload["data"]["output"][0]["type"] == "error"
    assert "approved product terminal commands" in payload["data"]["output"][0]["value"].lower()
