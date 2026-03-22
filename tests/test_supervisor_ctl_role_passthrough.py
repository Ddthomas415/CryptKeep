import scripts.supervisor_ctl as mod


def test_start_passes_admin_role(monkeypatch):
    captured = {}

    class Resolution:
        host = ""
        requested_port = 8501
        resolved_port = 8501
        requested_available = True
        auto_switched = False

    def fake_start(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(mod, "start", fake_start)
    monkeypatch.setattr(mod, "status", lambda: {"ok": True})
    monkeypatch.setattr(mod, "stop", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(mod, "resolve_preferred_port", lambda *a, **k: Resolution())
    monkeypatch.setattr(mod.argparse.ArgumentParser, "parse_args", lambda self: type("A", (), {
        "cmd": "start", "host": "", "port": 8501, "interval": 15, "hard": False
    })())

    rc = mod.main()
    assert rc == 0
    assert captured["current_role"] == "ADMIN"


def test_stop_passes_admin_role(monkeypatch):
    captured = {}

    def fake_stop(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(mod, "start", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(mod, "status", lambda: {"ok": True})
    monkeypatch.setattr(mod, "stop", fake_stop)
    monkeypatch.setattr(mod.argparse.ArgumentParser, "parse_args", lambda self: type("A", (), {
        "cmd": "stop", "host": "", "port": 8501, "interval": 15, "hard": True
    })())

    rc = mod.main()
    assert rc == 0
    assert captured["current_role"] == "ADMIN"
