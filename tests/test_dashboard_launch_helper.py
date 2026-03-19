from __future__ import annotations

from services.app import dashboard_launch as launch


def test_resolve_dashboard_launch_uses_next_available_port(monkeypatch) -> None:
    monkeypatch.setattr(
        launch,
        "resolve_preferred_port",
        lambda host, preferred_port, max_offset=50: type(
            "Resolution",
            (),
            {
                "host": host,
                "requested_port": int(preferred_port),
                "resolved_port": 8510,
                "requested_available": False,
                "auto_switched": True,
            },
        )(),
    )

    out = launch.resolve_dashboard_launch(host="127.0.0.1", preferred_port=8502, search_limit=25)

    assert out.host == "127.0.0.1"
    assert out.requested_port == 8502
    assert out.resolved_port == 8510
    assert out.auto_switched is True
    assert out.url == "http://127.0.0.1:8510"
    assert out.app_path.endswith("dashboard/app.py")


def test_dashboard_streamlit_cmd_and_env_use_resolved_port() -> None:
    ctx = launch.DashboardLaunchContext(
        host="127.0.0.1",
        requested_port=8502,
        resolved_port=8510,
        requested_available=False,
        auto_switched=True,
        url="http://127.0.0.1:8510",
        app_path="/tmp/dashboard/app.py",
    )

    cmd = launch.dashboard_streamlit_cmd(ctx, python_executable="/tmp/python", headless=True)
    env = launch.dashboard_streamlit_env(ctx, base_env={"EXISTING": "1"}, headless=True)

    assert cmd == [
        "/tmp/python",
        "-m",
        "streamlit",
        "run",
        "/tmp/dashboard/app.py",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        "8510",
        "--server.headless",
        "true",
    ]
    assert env["STREAMLIT_SERVER_ADDRESS"] == "127.0.0.1"
    assert env["STREAMLIT_SERVER_PORT"] == "8510"
    assert env["STREAMLIT_SERVER_HEADLESS"] == "true"
    assert env["EXISTING"] == "1"
