"""Concrete adapter + frozen controller wiring, synthetic external state only."""
from types import SimpleNamespace

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research.companion_runtime_adapter import PinnedRuntimeAdapter
from tests.test_companion_runtime_adapter import FakeDocker, make_pins


class WiringDocker(FakeDocker):
    def command(self, args, **kwargs):
        result = super().command(args, **kwargs)
        if args[:2] in (("container", "start"), ("container", "stop")):
            row = next(row for row in self.rows.values() if row["id"] == args[-1])
            if args[1] == "start":
                row.update(state="running", started="2026-10-16T21:12:00Z")
            else:
                row["state"] = "exited"
        return result


class Inline:
    def call(self, fn, args, timeout):
        assert 0 < timeout <= 45
        return fn(*args)


@pytest.mark.parametrize("risk_open", [False, True])
@pytest.mark.parametrize("created_apps", [False, True])
def test_real_backend_method_contract_in_controller(tmp_path, monkeypatch, risk_open, created_apps):
    import socket
    def forbidden(*args, **kwargs):
        pytest.fail("synthetic wiring attempted a real connection")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(core, "_CHILD_CONTEXT", True)
    docker = WiringDocker()
    if created_apps:
        for name in core.TARGETS[3:]:
            docker.rows[name].update(state="created", started="0001-01-01T00:00:00Z")
    runtime = PinnedRuntimeAdapter(docker, make_pins(docker), service_token="SYNTHETIC_ONLY", enabled=True)
    responses = {
        (6333, "/collections/documents"): {"status": "ok"},
        (8009, "/healthz"): {"service": "audit-log", "ok": True},
        (8009, "/v1/audit/events/recent?limit=1"): {"ok": True, "events": []},
        (8008, "/healthz"): {"service": "risk-stub", "ok": True, "no_trading": True},
        (8008, "/v1/risk/status"): {"gate": "NO_TRADING", "allow_trading": risk_open, "execution_mode": "DISABLED"},
        (8007, "/healthz"): {"service": "memory-retrieval", "ok": True, "db": True, "qdrant": True,
                              "minio": True, "memory_read_only_startup": True},
        (8002, "/healthz"): {"service": "orchestrator", "ok": True, "no_trading": True, "openai_enabled": False},
    }
    monkeypatch.setattr(runtime, "_http", lambda *a, **k: b"ready")
    monkeypatch.setattr(runtime, "_json", lambda port, path, **kw: responses[port, path])
    raw = {"asset": "BTC", "probe_protocol": core.PROTOCOL, "current_cause": "Synthetic stored context.",
           "assistant_status": {"provider": "fallback"}, "execution_disabled": True,
           "execution": {"enabled": False}, "risk_posture": responses[8008, "/v1/risk/status"],
           "evidence": [{"document_id": 42}]}
    queries = []
    def query(token):
        assert token == "SYNTHETIC_ONLY"
        queries.append(1)
        return {"raw": raw, "normalized": raw, "http_status": 200, "diagnostics": []}
    monkeypatch.setattr(core, "dashboard_probe", query)
    clock = SimpleNamespace(now=0)
    def settle(seconds):
        clock.now += seconds
    receipt = core.Receipt(tmp_path / "wiring.jsonl")
    try:
        runner = core.ExistingStackController(runtime, receipt, executor=Inline(), clock=lambda: clock.now, sleep=settle)
        result = runner.run(authorized=True)
    finally:
        receipt.close()
        runtime.close()
    assert result["query_passed"] is not risk_open
    assert len(queries) == (0 if risk_open else 1)
    assert all(row["state"] == ("exited" if risk_open else "running") for row in docker.rows.values())
    if risk_open:
        assert result["cleanup_verified"] is True
    assert "SYNTHETIC_ONLY" not in (tmp_path / "wiring.jsonl").read_text()
