from __future__ import annotations

import importlib
import signal


def _reload_bot_process():
    import services.os.app_paths as app_paths
    import services.process.bot_process as bp

    importlib.reload(app_paths)
    importlib.reload(bp)
    return bp


def test_start_bot_returns_ok_false_when_already_running(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    bp = _reload_bot_process()

    monkeypatch.setattr(bp, "status", lambda: {"ok": True, "running": True, "pid": 222})

    out = bp.start_bot(venue="coinbase", symbols=["BTC/USD"], force=False)

    assert out.get("ok") is False
    assert out.get("reason") == "already_running"
    assert out.get("pid") == 222


def test_start_bot_uses_code_root_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    bp = _reload_bot_process()

    monkeypatch.setattr(bp, "status", lambda: {"ok": True, "running": False})
    monkeypatch.setattr(bp, "code_root", lambda: tmp_path / "repo")
    monkeypatch.setattr(bp, "_write", lambda _obj: None)

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 9753

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["cwd"] = kwargs.get("cwd")
        return _DummyProc()

    monkeypatch.setattr(bp.subprocess, "Popen", _fake_popen)

    out = bp.start_bot(venue="coinbase", symbols=["BTC/USD"], force=False)

    assert out.get("ok") is True
    assert captured["cmd"] == [
        bp.sys.executable,
        "scripts/run_bot_safe.py",
        "--venue",
        "coinbase",
        "--symbols",
        "BTC/USD",
    ]
    assert captured["cwd"] == str(tmp_path / "repo")


def test_stop_bot_posix_soft_then_hard(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    bp = _reload_bot_process()

    monkeypatch.setattr(bp, "_read", lambda: {"pid": 1234})
    monkeypatch.setattr(bp.os, "name", "posix", raising=False)

    alive = iter([True, True, False])
    monkeypatch.setattr(bp, "_pid_alive", lambda _pid: next(alive))
    monkeypatch.setattr(bp.time, "sleep", lambda _s: None)

    writes: list[dict] = []
    monkeypatch.setattr(bp, "_write", lambda obj: writes.append(dict(obj)))

    kills: list[tuple[int, int]] = []
    monkeypatch.setattr(bp.os, "kill", lambda pid, sig: kills.append((int(pid), int(sig))))

    out = bp.stop_bot(hard=True)

    assert out.get("ok") is True
    assert out.get("stopped") is True
    assert kills == [(1234, int(signal.SIGTERM)), (1234, int(signal.SIGKILL))]
    assert writes and writes[-1] == {}


def test_stop_bot_posix_soft_only(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    bp = _reload_bot_process()

    monkeypatch.setattr(bp, "_read", lambda: {"pid": 4321})
    monkeypatch.setattr(bp.os, "name", "posix", raising=False)

    alive = iter([True, False])
    monkeypatch.setattr(bp, "_pid_alive", lambda _pid: next(alive))
    monkeypatch.setattr(bp.time, "sleep", lambda _s: None)

    writes: list[dict] = []
    monkeypatch.setattr(bp, "_write", lambda obj: writes.append(dict(obj)))

    kills: list[tuple[int, int]] = []
    monkeypatch.setattr(bp.os, "kill", lambda pid, sig: kills.append((int(pid), int(sig))))

    out = bp.stop_bot(hard=False)

    assert out.get("ok") is True
    assert out.get("stopped") is True
    assert kills == [(4321, int(signal.SIGTERM))]
    assert writes and writes[-1] == {}


def test_status_marks_legacy_compatibility(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    bp = _reload_bot_process()

    monkeypatch.setattr(bp, "_read", lambda: {})

    out = bp.status()

    assert out.get("compatibility_only") is True
    assert out.get("mode") == "legacy_compatibility"
    assert out.get("canonical_surface") == {
        "start": "scripts/start_bot.py",
        "stop": "scripts/stop_bot.py",
        "status": "scripts/bot_status.py",
    }
