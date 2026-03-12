def test_health_endpoints() -> None:
    from backend.app.api.routes.health import deps, live, ready

    live_payload = live()
    ready_payload = ready()
    deps_payload = deps()

    assert live_payload["status"] == "ok"
    assert ready_payload["status"] == "ok"
    assert deps_payload["status"] == "ok"
    assert deps_payload["checks"]["db"] in {"ok", "unavailable"}
