from __future__ import annotations

import json

from scripts import run_crypto_edge_collector_loop as script


def test_run_crypto_edge_collector_loop_requests_stop(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "request_stop", lambda: {"ok": True, "stop_file": "/tmp/stop"})
    monkeypatch.setattr(script.sys, "argv", ["run_crypto_edge_collector_loop.py", "--stop"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["stop_file"] == "/tmp/stop"


def test_run_crypto_edge_collector_loop_shows_status(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "load_runtime_status", lambda: {"ok": True, "status": "running", "pid": 12345})
    monkeypatch.setattr(script.sys, "argv", ["run_crypto_edge_collector_loop.py", "--status"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["status"] == "running"
    assert out["pid"] == 12345


def test_run_crypto_edge_collector_loop_runs_with_cfg(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _run_forever(cfg, *, max_loops=None):
        seen["cfg"] = cfg
        seen["max_loops"] = max_loops
        return {"ok": True, "status": "stopped", "reason": "max_loops", "loops": 2}

    monkeypatch.setattr(script, "run_forever", _run_forever)
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_crypto_edge_collector_loop.py",
            "--plan-file",
            "sample_data/crypto_edges/live_collector_plan.json",
            "--interval-sec",
            "15",
            "--max-loops",
            "2",
            "--source",
            "live_public",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["reason"] == "max_loops"
    assert seen["max_loops"] == 2
    cfg = seen["cfg"]
    assert getattr(cfg, "plan_file") == "sample_data/crypto_edges/live_collector_plan.json"
    assert getattr(cfg, "poll_interval_sec") == 15.0
    assert getattr(cfg, "source") == "live_public"
