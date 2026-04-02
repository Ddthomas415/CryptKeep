from __future__ import annotations

import importlib


def _reload_supervisor_process():
    import services.os.app_paths as app_paths
    import services.process.supervisor_process as sp

    importlib.reload(app_paths)
    importlib.reload(sp)
    return sp


def test_supervisor_process_start_reports_ok_false_when_already_running(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    sp = _reload_supervisor_process()

    monkeypatch.setattr(
        sp,
        "status",
        lambda: {
            "ok": True,
            "running": True,
            "cockpit": {"pid": 111, "alive": True},
            "watchdog": {"pid": 0, "alive": False},
        },
    )

    out = sp.start(
        streamlit_cmd=["python", "-m", "streamlit", "run", "dashboard/app.py"],
        watchdog_cmd=["python", "scripts/watchdog.py", "--loop"],
        cwd=tmp_path,
        current_role="ADMIN",
    )

    assert out.get("ok") is False
    assert out.get("reason") == "already_running"
    assert out.get("running") is True
