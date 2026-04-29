from __future__ import annotations

import importlib
import json


def _reload_process_manager():
    import services.os.app_paths as app_paths
    import services.bot.process_manager as process_manager

    importlib.reload(app_paths)
    importlib.reload(process_manager)
    return process_manager


def test_process_manager_is_marked_compatibility_only(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    pm = _reload_process_manager()

    assert pm.COMPATIBILITY_ONLY is True
    assert pm.CANONICAL_CONTROL_SURFACE == {
        "start": "scripts/start_bot.py",
        "stop": "scripts/stop_bot.py",
        "status": "scripts/bot_status.py",
    }


def test_start_process_returns_existing_running_status(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    pm = _reload_process_manager()
    existing = pm.ProcStatus(True, 321, "paper", 123, "python -m services.bot.cli_paper", "/tmp/paper.log", note="started")

    monkeypatch.setattr(pm, "read_status", lambda: existing)

    out = pm.start_process("paper", "services.bot.cli_paper")

    assert out.running is True
    assert out.pid == 321
    assert out.note == "already_running"


def test_stop_process_clears_stale_pid_status_file(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    pm = _reload_process_manager()
    pm.STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    pm.STATUS_PATH.write_text(
        json.dumps(
            {
                "pid": 999999,
                "mode": "paper",
                "started_ts_ms": 1,
                "cmd": "python -m services.bot.cli_paper",
                "log_path": str(tmp_path / "paper.log"),
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(pm, "_pid_is_running", lambda _pid: False)

    out = pm.stop_process()

    assert out.running is False
    assert out.note == "stale_pid_cleared"
    assert not pm.STATUS_PATH.exists()


def test_start_process_uses_code_root_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    pm = _reload_process_manager()

    first = pm.ProcStatus(False, None, None, None, None, None, note="no_status_file")
    second = pm.ProcStatus(
        True,
        2468,
        "paper",
        1,
        "python -m services.bot.cli_paper",
        str(tmp_path / "logs" / "paper_bot.log"),
        note="started",
    )
    states = [first, second]
    monkeypatch.setattr(pm, "read_status", lambda: states.pop(0))
    monkeypatch.setattr(pm, "_write_status", lambda _d: None)
    monkeypatch.setattr(pm, "code_root", lambda: tmp_path / "repo")

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 2468

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["cwd"] = kwargs.get("cwd")
        return _DummyProc()

    monkeypatch.setattr(pm.subprocess, "Popen", _fake_popen)

    out = pm.start_process("paper", "services.bot.cli_paper")

    assert out.running is True
    assert out.pid == 2468
    assert captured["cmd"] == [pm.sys.executable, "-m", "services.bot.cli_paper"]
    assert captured["cwd"] == str(tmp_path / "repo")
