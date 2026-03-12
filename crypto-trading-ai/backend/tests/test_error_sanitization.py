from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_validation_errors_do_not_echo_request_input_or_secrets() -> None:
    secret_marker = "SUPER_SECRET_MARKER_123"
    response = client.post(
        "/api/v1/connections/exchanges/test",
        json={
            "provider": "coinbase",
            "environment": "live",
            "credentials": {
                "api_key": {"nested": secret_marker},
                "api_secret": secret_marker,
                "passphrase": secret_marker,
            },
        },
    )
    assert response.status_code == 422

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(payload["error"]["details"]["errors"], list)

    for item in payload["error"]["details"]["errors"]:
        assert "input" not in item

    serialized = str(payload)
    assert secret_marker not in serialized

