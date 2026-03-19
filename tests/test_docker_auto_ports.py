from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[1]
    path = root / "docker" / "run_compose_auto_ports.py"
    spec = importlib.util.spec_from_file_location("cbp_docker_auto_ports", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_compose_port_env_keeps_requested_ports_when_free(monkeypatch) -> None:
    mod = _load_module()
    monkeypatch.setattr(
        mod,
        "resolve_preferred_port",
        lambda host, preferred_port, max_offset=50: type(
            "Resolution",
            (),
            {
                "host": host,
                "requested_port": int(preferred_port),
                "resolved_port": int(preferred_port),
                "requested_available": True,
                "auto_switched": False,
            },
        )(),
    )

    out = mod.resolve_compose_port_env({})

    assert out == {
        "BACKEND_HOST_PORT": "9000",
        "DASHBOARD_HOST_PORT": "18501",
    }


def test_resolve_compose_port_env_switches_busy_ports_and_dedupes(monkeypatch) -> None:
    mod = _load_module()

    def fake_resolve(host, preferred_port, max_offset=50):
        preferred = int(preferred_port)
        if preferred == 9000:
            resolved = 19000
        elif preferred == 18501:
            resolved = 19000
        elif preferred == 19001:
            resolved = 19001
        else:
            resolved = preferred
        return type(
            "Resolution",
            (),
            {
                "host": host,
                "requested_port": preferred,
                "resolved_port": resolved,
                "requested_available": resolved == preferred,
                "auto_switched": resolved != preferred,
            },
        )()

    monkeypatch.setattr(mod, "resolve_preferred_port", fake_resolve)

    out = mod.resolve_compose_port_env({})

    assert out["BACKEND_HOST_PORT"] == "19000"
    assert out["DASHBOARD_HOST_PORT"] == "19001"
