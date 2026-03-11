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


def test_stop_process_not_running():
    out = ps.stop_process("does_not_exist")
    assert out.get("ok") is True
    assert out.get("note") == "not_running"


def test_status_shape(monkeypatch):
    monkeypatch.setattr(ps, "is_running", lambda name: name == "a")
    monkeypatch.setattr(ps, "_read_pid", lambda name: 11 if name == "a" else None)
    out = ps.status(["a", "b"])
    assert out["a"]["running"] is True
    assert out["a"]["pid"] == 11
    assert out["b"]["running"] is False
    assert out["b"]["pid"] is None
