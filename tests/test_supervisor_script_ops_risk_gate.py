from __future__ import annotations

import sys

import scripts.supervisor as mod


def test_start_enforces_risk_gate(monkeypatch):
    calls = {}

    def fake_start(**kwargs):
        calls.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(mod, "start", fake_start)
    monkeypatch.setattr(mod, "stop", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(mod, "status", lambda: {"ok": True})
    monkeypatch.setattr(sys, "argv", ["supervisor.py", "start"])

    rc = mod.main()
    assert rc == 0
    assert calls.get("start_risk_gate") is True


def test_stop_enforces_risk_gate(monkeypatch):
    calls = {}

    def fake_stop(**kwargs):
        calls.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(mod, "start", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(mod, "stop", fake_stop)
    monkeypatch.setattr(mod, "status", lambda: {"ok": True})
    monkeypatch.setattr(sys, "argv", ["supervisor.py", "stop"])

    rc = mod.main()
    assert rc == 0
    assert calls.get("stop_risk_gate") is True
