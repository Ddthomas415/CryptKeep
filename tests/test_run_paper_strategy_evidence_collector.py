from __future__ import annotations

import json

from scripts import run_paper_strategy_evidence_collector as script


def test_run_paper_strategy_evidence_collector_requests_stop(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "request_stop", lambda: {"ok": True, "stop_file": "/tmp/paper_strategy_evidence.stop"})
    monkeypatch.setattr(script.sys, "argv", ["run_paper_strategy_evidence_collector.py", "--stop"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["stop_file"] == "/tmp/paper_strategy_evidence.stop"


def test_run_paper_strategy_evidence_collector_shows_status(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "load_runtime_status", lambda: {"ok": True, "status": "running", "pid": 67890})
    monkeypatch.setattr(script.sys, "argv", ["run_paper_strategy_evidence_collector.py", "--status"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "running"
    assert out["pid"] == 67890


def test_run_paper_strategy_evidence_collector_runs_with_cfg(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _run_campaign(cfg, *, max_strategies=None):
        seen["cfg"] = cfg
        seen["max_strategies"] = max_strategies
        return {"ok": True, "status": "completed", "reason": "completed"}

    monkeypatch.setattr(script, "run_campaign", _run_campaign)
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_paper_strategy_evidence_collector.py",
            "--strategies",
            "ema_cross,breakout_donchian",
            "--runtime-sec",
            "60",
            "--symbol",
            "ETH/USD",
            "--venue",
            "kraken",
            "--tick-interval-sec",
            "1.5",
            "--max-strategies",
            "1",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "completed"
    cfg = seen["cfg"]
    assert getattr(cfg, "strategies") == ("ema_cross", "breakout_donchian")
    assert getattr(cfg, "per_strategy_runtime_sec") == 60.0
    assert getattr(cfg, "symbol") == "ETH/USD"
    assert getattr(cfg, "venue") == "kraken"
    assert getattr(cfg, "tick_publish_interval_sec") == 1.5
    assert seen["max_strategies"] == 1
