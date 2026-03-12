from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_research_explain() -> None:
    response = client.post(
        "/api/v1/research/explain",
        json={"asset": "SOL", "question": "Why is SOL moving?"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["asset"] == "SOL"
    assert payload["data"]["question"] == "Why is SOL moving?"
    assert payload["data"]["execution_disabled"] is True
    assert isinstance(payload["data"]["evidence"], list)


def test_research_search() -> None:
    response = client.post(
        "/api/v1/research/search",
        json={"query": "SOL ecosystem", "asset": "SOL", "page": 1, "page_size": 20},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert "items" in payload["data"]
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["page_size"] == 20
