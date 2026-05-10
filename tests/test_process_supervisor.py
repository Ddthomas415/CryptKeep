from __future__ import annotations

from services.runtime import process_supervisor as ps


def test_is_running_clears_stale_pid(monkeypatch):
    called = {"cleared": 0}
    monkeypatch.setattr(ps, "_read_pid", lambda _name: 424242)
    monkeypatch.setattr(ps, "_clear_pid", lambda _name: called.__setitem__("cleared", called["cleared"] + 1))

    def _raise(_pid, _sig):
        raise OSError("dead")

    monkeypatch.setattr(ps.os, "kill", _raise)
    assert ps.is_running("x") is False
    assert called["cleared"] == 1


def test_start_process_already_running(monkeypatch):
    monkeypatch.setattr(ps, "is_running", lambda _name: True)
    monkeypatch.setattr(ps, "_read_pid", lambda _name: 777)
    out = ps.start_process("worker", ["python3", "fake.py"])
    assert out.get("ok") is True
    assert out.get("note") == "already_running"
    assert out.get("pid") == 777


def test_start_process_uses_code_root_as_cwd(monkeypatch, tmp_path):
    monkeypatch.setattr(ps, "is_running", lambda _name: False)
    monkeypatch.setattr(ps, "code_root", lambda: tmp_path)
    monkeypatch.setattr(ps, "_write_pid", lambda _name, _pid: None)

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 12345

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["cwd"] = kwargs.get("cwd")
        return _DummyProc()

    monkeypatch.setattr(ps.subprocess, "Popen", _fake_popen)

    out = ps.start_process("worker", ["python3", "fake.py"])

    assert out.get("ok") is True
    assert captured["cmd"] == ["python3", "fake.py"]
    assert captured["cwd"] == str(tmp_path)


def test_start_process_merges_custom_env(monkeypatch, tmp_path):
    monkeypatch.setattr(ps, "is_running", lambda _name: False)
    monkeypatch.setattr(ps, "code_root", lambda: tmp_path)
    monkeypatch.setattr(ps, "_write_pid", lambda _name, _pid: None)
    monkeypatch.setenv("CBP_BASE_ENV", "base")

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 12345

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["env"] = dict(kwargs.get("env") or {})
        return _DummyProc()

    monkeypatch.setattr(ps.subprocess, "Popen", _fake_popen)

    out = ps.start_process("worker", ["python3", "fake.py"], env={"CBP_SYMBOLS": "BTC/USD,ETH/USD"})

    assert out.get("ok") is True
    assert captured["cmd"] == ["python3", "fake.py"]
    assert captured["env"]["CBP_BASE_ENV"] == "base"
    assert captured["env"]["CBP_SYMBOLS"] == "BTC/USD,ETH/USD"


def test_stop_process_not_running():
    out = ps.stop_process("does_not_exist")
    assert out.get("ok") is True
    assert out.get("note") == "not_running"


def test_request_system_guard_halt_writes_halting(monkeypatch):
    calls: list[dict[str, str]] = []

    def _set_state(state, *, writer, reason):
        calls.append({"state": state, "writer": writer, "reason": reason})
        return {"state": state, "writer": writer, "reason": reason}

    monkeypatch.setattr(ps, "set_system_guard_state", _set_state)

    out = ps.request_system_guard_halt(writer="bot_runner", reason="shutdown")

    assert out["ok"] is True
    assert out["payload"]["state"] == "HALTING"
    assert calls == [{"state": "HALTING", "writer": "bot_runner", "reason": "shutdown"}]


def test_request_system_guard_halt_surfaces_write_failure(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(ps, "set_system_guard_state", _raise)

    out = ps.request_system_guard_halt(writer="bot_runner", reason="shutdown")

    assert out["ok"] is False
    assert out["reason"] == "system_guard_write_failed:RuntimeError"
    assert out["error"] == "disk full"


def test_status_shape(monkeypatch):
    monkeypatch.setattr(ps, "is_running", lambda name: name == "a")
    monkeypatch.setattr(ps, "_read_pid", lambda name: 11 if name == "a" else None)
    out = ps.status(["a", "b"])
    assert out["a"]["running"] is True
    assert out["a"]["pid"] == 11
    assert out["b"]["running"] is False
    assert out["b"]["pid"] is None
