from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_market_snapshot_contract() -> None:
    response = client.get("/api/v1/market/BTC/snapshot", params={"exchange": "coinbase"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["error"] is None
    assert payload["data"]["asset"] == "BTC"
    assert payload["data"]["exchange"] == "coinbase"
    assert float(payload["data"]["last_price"]) > 0
    assert float(payload["data"]["bid"]) <= float(payload["data"]["ask"])
    assert payload["data"]["timestamp"].endswith("Z")


def test_market_candles_contract() -> None:
    response = client.get(
        "/api/v1/market/SOL/candles",
        params={"exchange": "coinbase", "interval": "1h", "limit": 6},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["error"] is None
    assert payload["data"]["asset"] == "SOL"
    assert payload["data"]["exchange"] == "coinbase"
    assert payload["data"]["interval"] == "1h"
    assert len(payload["data"]["candles"]) == 6

    first = payload["data"]["candles"][0]
    assert set(first) == {"timestamp", "open", "high", "low", "close", "volume"}
    assert float(first["high"]) >= float(first["low"])
    assert float(payload["data"]["candles"][-1]["close"]) > 0
