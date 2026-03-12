from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
SENSITIVE_KEYS = {"api_key", "api_secret", "passphrase", "secret", "credential", "credentials"}


def _assert_no_sensitive_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert key.lower() not in SENSITIVE_KEYS
            _assert_no_sensitive_keys(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_no_sensitive_keys(nested)


def test_list_exchanges() -> None:
    response = client.get("/api/v1/connections/exchanges")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert "items" in payload["data"]
    assert len(payload["data"]["items"]) >= 1
    _assert_no_sensitive_keys(payload)


def test_test_exchange() -> None:
    response = client.post(
        "/api/v1/connections/exchanges/test",
        json={
            "provider": "coinbase",
            "environment": "live",
            "credentials": {
                "api_key": "demo",
                "api_secret": "demo",
                "passphrase": "demo",
            },
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["success"] is True
    assert "permissions" in payload["data"]
    _assert_no_sensitive_keys(payload)


def test_test_exchange_invalid_provider_validation() -> None:
    response = client.post(
        "/api/v1/connections/exchanges/test",
        json={
            "provider": "kucoin",
            "environment": "live",
            "credentials": {
                "api_key": "demo",
                "api_secret": "demo",
                "passphrase": "demo",
            },
        },
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    for error in payload["error"]["details"]["errors"]:
        assert "input" not in error


def test_save_exchange() -> None:
    response = client.post(
        "/api/v1/connections/exchanges",
        json={
            "provider": "coinbase",
            "label": "Main Coinbase",
            "environment": "live",
            "credentials": {
                "api_key": "demo",
                "api_secret": "demo",
                "passphrase": "demo",
            },
            "permissions": {
                "read_only": True,
                "allow_live_trading": False,
            },
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["provider"] == "coinbase"
    assert payload["data"]["label"] == "Main Coinbase"
    _assert_no_sensitive_keys(payload)


def test_save_exchange_invalid_environment_for_provider_validation() -> None:
    response = client.post(
        "/api/v1/connections/exchanges",
        json={
            "provider": "okx",
            "label": "Main OKX",
            "environment": "sandbox",
            "credentials": {
                "api_key": "demo",
                "api_secret": "demo",
                "passphrase": "demo",
            },
            "permissions": {
                "read_only": True,
                "allow_live_trading": False,
            },
        },
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "VALIDATION_ERROR"
