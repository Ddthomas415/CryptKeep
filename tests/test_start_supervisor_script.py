from __future__ import annotations

from scripts import start_supervisor


def test_start_supervisor_noop_when_existing_pid_alive(monkeypatch, tmp_path):
    state_data = tmp_path / "state" / "data"
    sup_dir = state_data / "supervisor"
    sup_dir.mkdir(parents=True, exist_ok=True)
    pid_path = sup_dir / "daemon.pid"
    pid_path.write_text("4242", encoding="utf-8")

    monkeypatch.setattr(start_supervisor, "ensure_dirs", lambda: None)
    monkeypatch.setattr(start_supervisor, "data_dir", lambda: state_data)
    monkeypatch.setattr(start_supervisor, "pid_alive", lambda _pid: True)
    monkeypatch.setattr(
        start_supervisor.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("should_not_spawn")),
    )

    assert start_supervisor.main() == 0
    assert pid_path.read_text(encoding="utf-8").strip() == "4242"


def test_start_supervisor_spawns_daemon_using_repo_root_cwd(monkeypatch, tmp_path):
    state_data = tmp_path / "state" / "data"
    sup_dir = state_data / "supervisor"
    sup_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(start_supervisor, "ensure_dirs", lambda: None)
    monkeypatch.setattr(start_supervisor, "data_dir", lambda: state_data)
    monkeypatch.setattr(start_supervisor, "pid_alive", lambda _pid: False)

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 9898

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["cwd"] = kwargs.get("cwd")
        return _DummyProc()

    monkeypatch.setattr(start_supervisor.subprocess, "Popen", _fake_popen)

    assert start_supervisor.main() == 0
    assert captured["cmd"] == [start_supervisor.sys.executable, "-u", "services/supervisor/supervisor_daemon.py"]
    assert captured["cwd"] == str(start_supervisor.ROOT)
    assert (sup_dir / "daemon.pid").read_text(encoding="utf-8").strip() == "9898"
