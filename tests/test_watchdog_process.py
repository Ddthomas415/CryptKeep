from __future__ import annotations

import importlib


def _reload_watchdog_process():
    import services.os.app_paths as app_paths
    import services.process.watchdog_process as wp

    importlib.reload(app_paths)
    importlib.reload(wp)
    return wp


def test_start_watchdog_uses_code_root_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    wp = _reload_watchdog_process()

    monkeypatch.setattr(wp, "status", lambda: {"ok": True, "running": False})
    monkeypatch.setattr(wp, "code_root", lambda: tmp_path / "repo")

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 1357

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["cwd"] = kwargs.get("cwd")
        return _DummyProc()

    monkeypatch.setattr(wp.subprocess, "Popen", _fake_popen)

    out = wp.start_watchdog(interval_sec=9)

    assert out.get("ok") is True
    assert captured["cmd"] == [wp.sys.executable, "scripts/watchdog.py", "--loop", "--interval", "9"]
    assert captured["cwd"] == str(tmp_path / "repo")


def test_start_watchdog_returns_already_running_when_status_running(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    wp = _reload_watchdog_process()

    monkeypatch.setattr(wp, "status", lambda: {"ok": True, "running": True, "pid": 777})

    out = wp.start_watchdog(interval_sec=10)

    assert out.get("ok") is False
    assert out.get("reason") == "already_running"
    assert out.get("pid") == 777
