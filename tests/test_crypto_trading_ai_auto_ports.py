from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[1]
    path = root / "crypto-trading-ai" / "scripts" / "run_compose_auto_ports.py"
    spec = importlib.util.spec_from_file_location("cta_auto_ports", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_compose_port_env_keeps_requested_ports_when_free(monkeypatch) -> None:
    mod = _load_module()
    monkeypatch.setattr(
        mod,
        "resolve_preferred_port",
        lambda host, preferred_port, max_offset=50: type("Resolution", (), {
            "host": host,
            "requested_port": int(preferred_port),
            "resolved_port": int(preferred_port),
            "requested_available": True,
            "auto_switched": False,
        })(),
    )

    out = mod.resolve_compose_port_env({})

    assert out == {
        "POSTGRES_HOST_PORT": "5432",
        "REDIS_HOST_PORT": "6379",
        "VECTOR_HOST_PORT": "6333",
        "BACKEND_HOST_PORT": "8000",
        "FRONTEND_HOST_PORT": "3000",
    }


def test_resolve_compose_port_env_switches_busy_ports_and_dedupes(monkeypatch) -> None:
    mod = _load_module()

    def fake_resolve(host, preferred_port, max_offset=50):
        preferred = int(preferred_port)
        if preferred == 5432:
            resolved = 15432
        elif preferred == 6379:
            resolved = 16379
        elif preferred == 6333:
            resolved = 16333
        elif preferred == 8000:
            resolved = 18000
        elif preferred == 3000:
            resolved = 18000
        elif preferred == 18001:
            resolved = 18001
        else:
            resolved = preferred
        return type("Resolution", (), {
            "host": host,
            "requested_port": preferred,
            "resolved_port": resolved,
            "requested_available": resolved == preferred,
            "auto_switched": resolved != preferred,
        })()

    monkeypatch.setattr(mod, "resolve_preferred_port", fake_resolve)

    out = mod.resolve_compose_port_env({})

    assert out["POSTGRES_HOST_PORT"] == "15432"
    assert out["REDIS_HOST_PORT"] == "16379"
    assert out["VECTOR_HOST_PORT"] == "16333"
    assert out["BACKEND_HOST_PORT"] == "18000"
    assert out["FRONTEND_HOST_PORT"] == "18001"
