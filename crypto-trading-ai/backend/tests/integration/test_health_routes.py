from backend.app.api.routes.health import deps, live, ready


def test_health_routes() -> None:
    for fn in (live, ready, deps):
        payload = fn()
        assert payload["status"] == "ok"
