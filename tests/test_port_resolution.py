from __future__ import annotations

from services.os import ports


def test_resolve_preferred_port_keeps_requested_when_available(monkeypatch) -> None:
    monkeypatch.setattr(ports, "can_bind", lambda host, port: int(port) == 8501)

    out = ports.resolve_preferred_port("127.0.0.1", 8501, max_offset=5)

    assert out.requested_port == 8501
    assert out.resolved_port == 8501
    assert out.requested_available is True
    assert out.auto_switched is False


def test_resolve_preferred_port_switches_to_next_available(monkeypatch) -> None:
    monkeypatch.setattr(ports, "can_bind", lambda host, port: int(port) == 8503)

    out = ports.resolve_preferred_port("127.0.0.1", 8501, max_offset=5)

    assert out.requested_port == 8501
    assert out.resolved_port == 8503
    assert out.requested_available is False
    assert out.auto_switched is True
