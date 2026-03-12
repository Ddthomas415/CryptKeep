from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.routes import health as health_route

client = TestClient(app)


def test_health_live() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "backend"


def test_health_ready() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "backend"


def test_health_deps() -> None:
    response = client.get("/health/deps")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert sorted(payload["checks"].keys()) == ["db", "redis", "vector_db"]
    assert payload["checks"]["db"] == "ok"
    assert payload["checks"]["redis"] == "ok"


def test_health_deps_degraded_when_dependency_fails(monkeypatch) -> None:
    monkeypatch.setattr(health_route, "_check_db", lambda: ("ok", None))
    monkeypatch.setattr(health_route, "_check_redis", lambda _url: ("error", "redis unavailable"))
    monkeypatch.setattr(health_route, "_check_vector", lambda _url: ("ok", None))

    payload = health_route.deps()

    assert payload["status"] == "degraded"
    assert payload["checks"]["redis"] == "error"
    assert payload["errors"]["redis"] == "redis unavailable"


def test_health_ready_reflects_dependency_state(monkeypatch) -> None:
    monkeypatch.setattr(health_route, "_check_db", lambda: ("ok", None))
    monkeypatch.setattr(health_route, "_check_redis", lambda _url: ("ok", None))
    monkeypatch.setattr(health_route, "_check_vector", lambda _url: ("error", "vector unavailable"))

    payload = health_route.ready()

    assert payload["status"] == "degraded"
    assert sorted(payload["checks"].keys()) == ["db", "redis", "vector_db"]
    assert payload["checks"]["vector_db"] == "error"


def test_health_dependency_errors_redact_url_credentials() -> None:
    raw = "dial tcp postgres://app:super_secret_password@db.internal:5432/trading_ai failed"
    redacted = health_route._sanitize_dependency_error(raw)
    assert redacted is not None
    assert "super_secret_password" not in redacted
    assert "://***:***@" in redacted


def test_health_dependency_errors_redact_key_value_secrets(monkeypatch) -> None:
    secret_marker = "ULTRA_SECRET_MARKER_456"
    monkeypatch.setattr(health_route, "_check_db", lambda: ("error", f"password={secret_marker}"))
    monkeypatch.setattr(health_route, "_check_redis", lambda _url: ("error", f"token={secret_marker}"))
    monkeypatch.setattr(health_route, "_check_vector", lambda _url: ("ok", None))

    payload = health_route.deps()

    assert payload["status"] == "degraded"
    serialized = str(payload)
    assert secret_marker not in serialized
    assert payload["errors"]["db"].endswith("***")
    assert payload["errors"]["redis"].endswith("***")
