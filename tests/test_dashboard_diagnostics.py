from __future__ import annotations

import sys

from services.app import dashboard_diagnostics as dd
from services.app.dashboard_launch import DashboardLaunchContext


class _RunningProc:
    def __init__(self) -> None:
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def kill(self):
        self.terminated = True
        self.returncode = -9


class _ExitedProc:
    def __init__(self, code: int = 1) -> None:
        self.returncode = code

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode

    def terminate(self):
        return None

    def kill(self):
        return None


def _ctx(port: int = 8502, resolved: int = 8503, *, auto_switched: bool = True) -> DashboardLaunchContext:
    return DashboardLaunchContext(
        host="127.0.0.1",
        requested_port=port,
        resolved_port=resolved,
        requested_available=not auto_switched,
        auto_switched=auto_switched,
        url=f"http://127.0.0.1:{resolved}",
        app_path="/tmp/dashboard/app.py",
    )


def test_run_dashboard_diagnostics_without_smoke_reports_port_note(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "streamlit", object())
    monkeypatch.setattr(dd, "dashboard_default_port", lambda: 8502)
    monkeypatch.setattr(dd, "dashboard_port_search_limit", lambda: 50)
    monkeypatch.setattr(dd, "resolve_dashboard_launch", lambda **kwargs: _ctx())
    monkeypatch.setattr(dd, "_compile_dashboard_sources", lambda: {"ok": True, "checked_files": 3, "failures": []})

    out = dd.run_dashboard_diagnostics(startup_smoke=False)

    assert out["ok"] is True
    assert out["status"] == "ok"
    assert out["requested_port"] == 8502
    assert out["resolved_port"] == 8503
    assert out["auto_switched"] is True
    assert "auto launcher can use 8503 instead" in out["notes"][0]


def test_run_dashboard_diagnostics_smoke_success(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "streamlit", object())
    monkeypatch.setattr(dd, "dashboard_default_port", lambda: 8502)
    monkeypatch.setattr(dd, "dashboard_port_search_limit", lambda: 50)
    monkeypatch.setattr(dd, "resolve_dashboard_launch", lambda **kwargs: _ctx(auto_switched=False, resolved=8502))
    monkeypatch.setattr(dd, "_compile_dashboard_sources", lambda: {"ok": True, "checked_files": 3, "failures": []})
    monkeypatch.setattr(dd, "dashboard_streamlit_cmd", lambda *args, **kwargs: ["python", "-m", "streamlit"])
    monkeypatch.setattr(dd, "dashboard_streamlit_env", lambda *args, **kwargs: {})
    monkeypatch.setattr(dd, "repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(dd, "port_open", lambda host, port: True)
    monkeypatch.setattr(dd.subprocess, "Popen", lambda *args, **kwargs: _RunningProc())

    out = dd.run_dashboard_diagnostics(startup_smoke=True, timeout_sec=1.0)

    assert out["ok"] is True
    assert out["smoke"]["attempted"] is True
    assert out["smoke"]["reachable"] is True
    assert out["smoke"]["classification"] == "reachable"


def test_run_dashboard_diagnostics_smoke_failure_captures_log(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "streamlit", object())
    monkeypatch.setattr(dd, "dashboard_default_port", lambda: 8502)
    monkeypatch.setattr(dd, "dashboard_port_search_limit", lambda: 50)
    monkeypatch.setattr(dd, "resolve_dashboard_launch", lambda **kwargs: _ctx(auto_switched=False, resolved=8502))
    monkeypatch.setattr(dd, "_compile_dashboard_sources", lambda: {"ok": True, "checked_files": 3, "failures": []})
    monkeypatch.setattr(dd, "dashboard_streamlit_cmd", lambda *args, **kwargs: ["python", "-m", "streamlit"])
    monkeypatch.setattr(dd, "dashboard_streamlit_env", lambda *args, **kwargs: {})
    monkeypatch.setattr(dd, "repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(dd, "port_open", lambda host, port: False)

    def fake_popen(*args, **kwargs):
        kwargs["stdout"].write("Traceback (most recent call last):\nImportError: bad import\n")
        kwargs["stdout"].flush()
        return _ExitedProc(1)

    monkeypatch.setattr(dd.subprocess, "Popen", fake_popen)

    out = dd.run_dashboard_diagnostics(startup_smoke=True, timeout_sec=1.0)

    assert out["ok"] is False
    assert out["status"] == "critical"
    assert out["smoke"]["attempted"] is True
    assert out["smoke"]["reachable"] is False
    assert out["smoke"]["classification"] in {"import_error", "startup_exception"}
    assert out["issues"][0]["category"] == "dashboard_smoke"


def test_run_dashboard_diagnostics_reachable_but_uncaught_error_is_failure(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "streamlit", object())
    monkeypatch.setattr(dd, "dashboard_default_port", lambda: 8502)
    monkeypatch.setattr(dd, "dashboard_port_search_limit", lambda: 50)
    monkeypatch.setattr(dd, "resolve_dashboard_launch", lambda **kwargs: _ctx(auto_switched=False, resolved=8502))
    monkeypatch.setattr(dd, "_compile_dashboard_sources", lambda: {"ok": True, "checked_files": 3, "failures": []})
    monkeypatch.setattr(dd, "dashboard_streamlit_cmd", lambda *args, **kwargs: ["python", "-m", "streamlit"])
    monkeypatch.setattr(dd, "dashboard_streamlit_env", lambda *args, **kwargs: {})
    monkeypatch.setattr(dd, "repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(dd, "port_open", lambda host, port: True)

    def fake_popen(*args, **kwargs):
        kwargs["stdout"].write("Uncaught app execution\nTraceback (most recent call last):\nModuleNotFoundError: No module named 'services.admin'\n")
        kwargs["stdout"].flush()
        return _RunningProc()

    monkeypatch.setattr(dd.subprocess, "Popen", fake_popen)

    out = dd.run_dashboard_diagnostics(startup_smoke=True, timeout_sec=1.0)

    assert out["ok"] is False
    assert out["smoke"]["reachable"] is True
    assert out["smoke"]["classification"] == "import_error"
    assert out["issues"][0]["category"] == "dashboard_smoke"
