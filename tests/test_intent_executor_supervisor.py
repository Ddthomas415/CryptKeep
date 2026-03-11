from __future__ import annotations

import importlib


def _reload_intent_executor_supervisor():
    import services.os.app_paths as app_paths
    import services.execution.intent_executor_supervisor as ies

    importlib.reload(app_paths)
    importlib.reload(ies)
    return ies


def test_intent_executor_supervisor_start_uses_code_root_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    ies = _reload_intent_executor_supervisor()

    monkeypatch.setattr(ies, "_read_pid", lambda: None)
    monkeypatch.setattr(ies, "_remove_pid", lambda: None)
    monkeypatch.setattr(ies, "_write_pid", lambda _pid: None)
    monkeypatch.setattr(ies, "code_root", lambda: tmp_path / "repo")

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 8642

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["cwd"] = kwargs.get("cwd")
        return _DummyProc()

    monkeypatch.setattr(ies.subprocess, "Popen", _fake_popen)

    out = ies.start()

    assert out.get("ok") is True
    assert out.get("pid") == 8642
    assert captured["cmd"] == [ies.sys.executable, "scripts/run_intent_executor.py"]
    assert captured["cwd"] == str(tmp_path / "repo")


def test_intent_executor_supervisor_start_already_running_shape(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    ies = _reload_intent_executor_supervisor()

    monkeypatch.setattr(ies, "_read_pid", lambda: 1111)
    monkeypatch.setattr(ies, "_pid_alive", lambda _pid: True)

    out = ies.start()

    assert out.get("ok") is True
    assert out.get("already_running") is True
    assert out.get("pid") == 1111
