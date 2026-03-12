from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module(name: str, relative_path: str):
    root = Path(__file__).resolve().parents[1]
    path = root / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_backend_binding_uses_next_free_port(monkeypatch) -> None:
    mod = _load_module("cta_local_dev_ports", "crypto-trading-ai/scripts/local_dev_ports.py")

    monkeypatch.setattr(
        mod,
        "resolve_preferred_port",
        lambda host, preferred_port, max_offset=50: mod.PortResolution(
            host=str(host),
            requested_port=int(preferred_port),
            resolved_port=8010,
            requested_available=False,
            auto_switched=True,
        ),
    )

    out = mod.resolve_backend_binding({"API_HOST": "0.0.0.0", "API_PORT": "8000"})

    assert out["host"] == "0.0.0.0"
    assert out["resolution"].requested_port == 8000
    assert out["resolution"].resolved_port == 8010
    assert out["resolution"].auto_switched is True


def test_resolve_frontend_binding_uses_saved_backend_port(monkeypatch, tmp_path) -> None:
    mod = _load_module("cta_local_dev_ports", "crypto-trading-ai/scripts/local_dev_ports.py")
    monkeypatch.setattr(mod, "PORT_STATE_PATH", tmp_path / "local_dev_ports.json")
    mod.save_runtime_ports({"backend_host": "127.0.0.1", "backend_port": 8010})

    monkeypatch.setattr(
        mod,
        "resolve_preferred_port",
        lambda host, preferred_port, max_offset=50: mod.PortResolution(
            host=str(host),
            requested_port=int(preferred_port),
            resolved_port=3001,
            requested_available=False,
            auto_switched=True,
        ),
    )

    out = mod.resolve_frontend_binding({"FRONTEND_HOST_PORT": "3000"})

    assert out["backend_url"] == "http://127.0.0.1:8010"
    assert out["resolution"].requested_port == 3000
    assert out["resolution"].resolved_port == 3001
