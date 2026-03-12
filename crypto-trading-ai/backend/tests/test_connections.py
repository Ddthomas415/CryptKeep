from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_list_exchanges() -> None:
    response = client.get("/api/v1/connections/exchanges")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert "items" in payload["data"]
    assert len(payload["data"]["items"]) >= 1


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
