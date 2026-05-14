from __future__ import annotations

import json

from scripts import report_supervised_soak_status as soak_report


def test_build_report_restores_paper_gate_truth_with_symbol_drift(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    flags = runtime / "flags"
    health = runtime / "health"
    flags.mkdir(parents=True, exist_ok=True)
    health.mkdir(parents=True, exist_ok=True)

    (flags / "bot_runner.status.json").write_text(
        json.dumps(
            {
                "ts_epoch": 1000.0,
                "state": {
                    "mode": "paper",
                    "live_enabled": False,
                    "venue": "coinbase",
                    "symbols": ["B3/USD", "B3/USDC"],
                    "with_reconcile": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (flags / "pipeline.status.json").write_text(
        json.dumps({"pid": 11, "loops": 12, "errors": 4, "last_ok": True, "last_reason": "multi_symbol_cycle", "symbols": ["B3/USD", "B3/USDC"]}),
        encoding="utf-8",
    )
    (flags / "intent_executor.status.json").write_text(
        json.dumps({"pid": 22, "loops": 34, "symbols": ["B3/USD", "B3/USDC"]}),
        encoding="utf-8",
    )
    (health / "managed_symbol_selection.json").write_text(
        json.dumps({"ok": True, "selected": ["BILL/USD", "BILL/USDC"], "source": "coinbase_movers"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(soak_report, "runtime_dir", lambda: runtime)
    monkeypatch.setattr(
        soak_report,
        "canonical_service_status",
        lambda: {
            "pipeline": {"running": True},
            "executor": {"running": True},
            "intent_consumer": {"running": False},
            "ops_signal_adapter": {"running": True},
            "ops_risk_gate": {"running": True},
            "reconciler": {"running": False},
            "ai_alert_monitor": {"running": True},
        },
    )
    monkeypatch.setattr(
        soak_report,
        "load_runtime_status",
        lambda: {"pid": 33, "status": "idle", "pid_alive": True, "incidents_written": 11, "last_severity": "warn", "reason": "no_new_events"},
    )
    monkeypatch.setattr(
        soak_report.rbr,
        "load_trading_cfg",
        lambda path="config/trading.yaml": {
            "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
            "live": {"exchange_id": "coinbase"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["B3/USD", "B3/USDC"],
        },
    )

    out = soak_report.build_report(now_epoch=1000.0 + 48 * 3600)

    assert out["counts_for_paper_gate"] is True
    assert out["topology_matches_run_state"] is True
    assert out["symbols"]["runtime_matches_run_state"] is True
    assert out["symbols"]["runtime_matches_current_desired_state"] is False
    assert out["current_desired_state"]["symbols"] == ["BILL/USD", "BILL/USDC"]
    assert out["ai_alert_monitor"]["status"] == "idle"


def test_build_report_does_not_count_safe_idle_service_as_valid_topology(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    flags = runtime / "flags"
    health = runtime / "health"
    flags.mkdir(parents=True, exist_ok=True)
    health.mkdir(parents=True, exist_ok=True)

    (flags / "bot_runner.status.json").write_text(
        json.dumps(
            {
                "ts_epoch": 1000.0,
                "state": {
                    "mode": "paper",
                    "live_enabled": False,
                    "venue": "coinbase",
                    "symbols": ["B3/USD", "B3/USDC"],
                    "with_reconcile": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (flags / "pipeline.status.json").write_text(
        json.dumps({"pid": 11, "status": "safe_idle", "symbols": ["B3/USD", "B3/USDC"]}),
        encoding="utf-8",
    )
    (flags / "intent_executor.status.json").write_text(
        json.dumps({"pid": 22, "loops": 34, "symbols": ["B3/USD", "B3/USDC"]}),
        encoding="utf-8",
    )

    monkeypatch.setattr(soak_report, "runtime_dir", lambda: runtime)
    monkeypatch.setattr(
        soak_report,
        "canonical_service_status",
        lambda: {
            "pipeline": {"running": False, "status": "safe_idle", "healthy": False},
            "executor": {"running": True},
            "intent_consumer": {"running": False},
            "ops_signal_adapter": {"running": True},
            "ops_risk_gate": {"running": True},
            "reconciler": {"running": False},
            "ai_alert_monitor": {"running": True},
        },
    )
    monkeypatch.setattr(
        soak_report,
        "load_runtime_status",
        lambda: {"pid": 33, "status": "idle", "pid_alive": True, "incidents_written": 0, "reason": "no_new_events"},
    )
    monkeypatch.setattr(
        soak_report.rbr,
        "load_trading_cfg",
        lambda path="config/trading.yaml": {
            "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
            "live": {"exchange_id": "coinbase"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["B3/USD", "B3/USDC"],
        },
    )

    out = soak_report.build_report(now_epoch=1000.0 + 3600.0)

    assert out["counts_for_paper_gate"] is False
    assert out["topology_matches_run_state"] is False
