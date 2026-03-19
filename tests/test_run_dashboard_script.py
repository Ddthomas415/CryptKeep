from __future__ import annotations

from scripts import run_dashboard as script


class _DummyProc:
    def __init__(self) -> None:
        self.returncode = 0
        self.terminated = False

    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.terminated = True


def test_run_dashboard_script_uses_auto_switched_port(monkeypatch, capsys) -> None:
    ctx = script.resolve_dashboard_launch(host="127.0.0.1", preferred_port=8502)
    ctx = type(ctx)(
        host=ctx.host,
        requested_port=8502,
        resolved_port=8504,
        requested_available=False,
        auto_switched=True,
        url="http://127.0.0.1:8504",
        app_path=ctx.app_path,
    )
    recorded: dict[str, object] = {}

    monkeypatch.setattr(script, "resolve_dashboard_launch", lambda **kwargs: ctx)
    monkeypatch.setattr(script, "dashboard_port_search_limit", lambda: 50)
    monkeypatch.setattr(script, "dashboard_default_port", lambda fallback=8502: 8502)
    monkeypatch.setattr(script, "dashboard_streamlit_cmd", lambda *_args, **_kwargs: ["python", "fake"])
    monkeypatch.setattr(script, "dashboard_streamlit_env", lambda *_args, **_kwargs: {"ENV": "1"})
    monkeypatch.setattr(script, "wait_for_dashboard", lambda *args, **kwargs: True)
    monkeypatch.setattr(script, "port_open", lambda *args, **kwargs: True)
    monkeypatch.setattr(script, "open_dashboard_browser", lambda launch_ctx: recorded.setdefault("opened", launch_ctx.url))
    monkeypatch.setattr(script, "repo_root", lambda: "/tmp/repo")

    def fake_popen(cmd, cwd=None, env=None):
        recorded["cmd"] = list(cmd)
        recorded["cwd"] = cwd
        recorded["env"] = dict(env or {})
        return _DummyProc()

    monkeypatch.setattr(script.subprocess, "Popen", fake_popen)

    rc = script.main(["--open", "--print-url"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "http://127.0.0.1:8504" in out
    assert "Requested dashboard port 8502 is busy. Using 8504 instead." in out
    assert recorded["cmd"] == ["python", "fake"]
    assert recorded["cwd"] == "/tmp/repo"
    assert recorded["env"] == {"ENV": "1"}
    assert recorded["opened"] == "http://127.0.0.1:8504"
