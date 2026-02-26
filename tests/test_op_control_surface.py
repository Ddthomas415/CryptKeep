from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import scripts.op as op


def _run_op(args: list[str]) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "scripts" / "op.py")] + args
    return subprocess.run(cmd, cwd=str(root), text=True, capture_output=True)


def test_op_preflight_json_shape():
    p = _run_op(["preflight"])
    assert p.stdout.strip()
    payload = json.loads(p.stdout)
    assert isinstance(payload.get("checks"), list)
    assert isinstance(payload.get("count"), int)
    # preflight may fail in some environments; shape is the contract.
    assert isinstance(payload.get("ok"), bool)


def test_op_status_and_logs_surface():
    p_list = _run_op(["list"])
    assert p_list.returncode == 0
    names = [x.strip() for x in p_list.stdout.splitlines() if x.strip()]
    assert names
    name = names[0]

    p_status = _run_op(["status", "--name", name])
    assert p_status.returncode == 0
    status_obj = json.loads(p_status.stdout)
    assert status_obj.get("name") == name
    assert "ok" in status_obj

    p_logs = _run_op(["logs", "--name", name, "--lines", "10"])
    # logs can be empty, but command should be callable.
    assert p_logs.returncode in (0, 2)


def test_op_supervisor_status_shape():
    p = _run_op(["supervisor-status"])
    assert p.stdout.strip()
    payload = json.loads(p.stdout)
    assert isinstance(payload.get("ok"), bool)
    assert "out" in payload


def test_op_service_ctl_all_aggregate(monkeypatch):
    monkeypatch.setattr(op, "_service_ctl_list", lambda: ["a", "b"])
    outcomes = {"a": {"ok": True}, "b": {"ok": False}}
    monkeypatch.setattr(op, "_service_ctl_call", lambda n, a, lines=None: {"name": n, "action": a, **outcomes[n]})
    payload = op._service_ctl_all("stop")
    assert payload.get("action") == "stop"
    assert payload.get("count") == 2
    assert payload.get("ok") is False


def test_op_stop_everything_precedence(monkeypatch):
    monkeypatch.setattr(op, "_script_call", lambda script, *args: {"ok": True, "script": script, "args": list(args)})
    monkeypatch.setattr(op, "_service_ctl_all", lambda action: {"ok": True, "action": action})
    monkeypatch.setattr(op, "_clean", lambda: {"ok": True})
    payload = op._stop_everything()
    assert payload.get("ok") is True
    assert payload.get("precedence") == [
        "bot_ctl.stop_all(hard)",
        "service_ctl.stop_all",
        "supervisor_ctl.stop(hard)",
        "stop_supervisor.flag",
        "watchdog_ctl.stop(hard)",
        "watchdog_ctl.clear_stale(hard)",
    ]
    assert payload.get("bot", {}).get("script") == "bot_ctl.py"
    assert payload.get("supervisor", {}).get("script") == "supervisor_ctl.py"
    assert payload.get("watchdog", {}).get("script") == "watchdog_ctl.py"
