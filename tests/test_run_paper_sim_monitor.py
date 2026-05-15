from __future__ import annotations

import json

from scripts import run_paper_sim_monitor as script


def test_run_paper_sim_monitor_requests_stop(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "request_stop", lambda: {"ok": True, "stop_file": "/tmp/paper_sim_monitor.stop"})
    monkeypatch.setattr(script.sys, "argv", ["run_paper_sim_monitor.py", "--stop"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["stop_file"] == "/tmp/paper_sim_monitor.stop"


def test_run_paper_sim_monitor_shows_status(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "load_runtime_status",
        lambda: {"ok": True, "status": "running", "campaign_status": "running", "pid": 45678},
    )
    monkeypatch.setattr(script.sys, "argv", ["run_paper_sim_monitor.py", "--status"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "running"
    assert out["pid"] == 45678


def test_run_paper_sim_monitor_registers_watch(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "register_watch",
        lambda *, name, trigger: {"ok": True, "name": name, "trigger": trigger},
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        ["run_paper_sim_monitor.py", "--register-watch", "next_fill", "--watch-trigger", "new_fill"],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["name"] == "next_fill"
    assert out["trigger"] == "new_fill"


def test_run_paper_sim_monitor_lists_watches(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "list_watches", lambda: [{"name": "next_fill", "trigger": "new_fill"}])
    monkeypatch.setattr(script.sys, "argv", ["run_paper_sim_monitor.py", "--list-watches"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["watches"][0]["name"] == "next_fill"


def test_run_paper_sim_monitor_deletes_watch(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "delete_watch", lambda *, name: {"ok": True, "name": name})
    monkeypatch.setattr(script.sys, "argv", ["run_paper_sim_monitor.py", "--delete-watch", "next_fill"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["name"] == "next_fill"


def test_run_paper_sim_monitor_collects_once(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _collect_once(cfg):
        seen["cfg"] = cfg
        return {"ok": True, "campaign_status": "completed", "recommendation": "enough_evidence"}

    monkeypatch.setattr(script, "collect_once", _collect_once)
    monkeypatch.setattr(
        script.sys,
        "argv",
        ["run_paper_sim_monitor.py", "--once", "--interval-sec", "30", "--min-closed-trades", "2"],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["recommendation"] == "enough_evidence"
    cfg = seen["cfg"]
    assert getattr(cfg, "poll_interval_sec") == 30.0
    assert getattr(cfg, "min_closed_trades_for_enough_evidence") == 2


def test_run_paper_sim_monitor_runs_with_cfg(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _run_forever(cfg, *, max_loops=None):
        seen["cfg"] = cfg
        seen["max_loops"] = max_loops
        return {"ok": True, "status": "stopped", "reason": "max_loops"}

    monkeypatch.setattr(script, "run_forever", _run_forever)
    monkeypatch.setattr(
        script.sys,
        "argv",
        ["run_paper_sim_monitor.py", "--interval-sec", "45", "--min-closed-trades", "3", "--max-loops", "1"],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["reason"] == "max_loops"
    cfg = seen["cfg"]
    assert getattr(cfg, "poll_interval_sec") == 45.0
    assert getattr(cfg, "min_closed_trades_for_enough_evidence") == 3
    assert seen["max_loops"] == 1
