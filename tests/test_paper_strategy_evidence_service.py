from __future__ import annotations

import json

from services.analytics import paper_strategy_evidence_service as svc


def test_run_campaign_writes_completed_status_and_persists_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    stop_calls: list[str] = []

    monkeypatch.setattr(
        svc,
        "_component_runtime",
        lambda name: {"name": name, "pid_alive": False, "pid": 0, "status": "not_started"},
    )
    monkeypatch.setattr(
        svc,
        "_ensure_component",
        lambda name, *, cfg: {"name": name, "started": True, "pid": 123 if name == "tick_publisher" else 456, "status": "running"},
    )
    monkeypatch.setattr(
        svc,
        "_run_strategy_window",
        lambda *, cfg, strategy_name: {
            "strategy": str(strategy_name),
            "runtime_sec": 1.0,
            "stop_reason": "runtime_elapsed",
            "runner_status": "stopped",
            "enqueued_total": 0,
            "fills_delta": 0,
            "closed_trades_delta": 0,
            "net_realized_pnl_delta": 0.0,
            "fills_total": 0,
            "closed_trades_total": 0,
            "net_realized_pnl_total": 0.0,
            "latest_fill_ts": "",
        },
    )
    monkeypatch.setattr(
        svc,
        "run_strategy_evidence_cycle",
        lambda **kwargs: {"as_of": "2026-03-19T00:00:00Z", "aggregate_leaderboard": {"rows": []}, "decisions": []},
    )
    monkeypatch.setattr(svc, "persist_strategy_evidence", lambda report: {"ok": True, "latest_path": str(tmp_path / "strategy_evidence.latest.json")})
    monkeypatch.setattr(
        svc,
        "write_decision_record",
        lambda report, *, artifact_path="": {"ok": True, "path": str(tmp_path / "decision_record.md"), "artifact_path": artifact_path},
    )
    monkeypatch.setattr(svc, "_wait_for_component_stop", lambda name, *, timeout_sec=10.0: True)
    monkeypatch.setattr(
        svc,
        "_stop_component",
        lambda name: stop_calls.append(name) or {"ok": True, "component": name},
    )

    out = svc.run_campaign(
        svc.PaperStrategyEvidenceServiceCfg(
            strategies=("ema_cross", "breakout_donchian"),
            per_strategy_runtime_sec=1.0,
        )
    )

    assert out["ok"] is True
    assert out["status"] == "completed"
    assert out["reason"] == "completed"
    assert out["completed_strategies"] == 2
    assert out["started_components"] == {"tick_publisher": 123, "paper_engine": 456}
    assert out["evidence"]["latest_path"].endswith("strategy_evidence.latest.json")
    assert out["decision_record"]["path"].endswith("decision_record.md")
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["status"] == "completed"
    assert status["completed_strategies"] == 2
    assert stop_calls.count("strategy_runner") >= 1
    assert "tick_publisher" in stop_calls
    assert "paper_engine" in stop_calls


def test_run_campaign_refuses_busy_strategy_runner(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    def _component_runtime(name: str) -> dict[str, object]:
        if name == "strategy_runner":
            return {"name": name, "pid_alive": True, "pid": 321, "status": "running"}
        return {"name": name, "pid_alive": False, "pid": 0, "status": "not_started"}

    monkeypatch.setattr(svc, "_component_runtime", _component_runtime)

    out = svc.run_campaign(svc.PaperStrategyEvidenceServiceCfg())

    assert out["ok"] is False
    assert out["status"] == "blocked"
    assert out["reason"] == "strategy_runner_busy"
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["status"] == "blocked"


def test_load_runtime_status_marks_dead_process(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.status_file().parent.mkdir(parents=True, exist_ok=True)
    svc.status_file().write_text(
        json.dumps(
            {
                "ok": True,
                "has_status": True,
                "status": "running",
                "ts": "2026-03-19T01:00:00Z",
                "strategies": ["ema_cross"],
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "per_strategy_runtime_sec": 60.0,
            }
        ),
        encoding="utf-8",
    )
    svc.pid_file().write_text(
        json.dumps(
            {
                "pid": 55555,
                "started_ts": "2026-03-19T00:59:00Z",
                "strategies": ["ema_cross"],
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "per_strategy_runtime_sec": 60.0,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(svc, "_process_alive", lambda pid: False)

    out = svc.load_runtime_status()

    assert out["ok"] is True
    assert out["status"] == "dead"
    assert out["reason"] == "process_not_running"
    assert out["pid"] == 55555
    assert out["pid_alive"] is False
