from __future__ import annotations

import importlib
import json
from pathlib import Path


def _reload_module(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import scripts.report_supervised_soak_status as mod

    importlib.reload(app_paths)
    return importlib.reload(mod)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_build_report_in_progress_paper_topology(monkeypatch, tmp_path):
    mod = _reload_module(monkeypatch, tmp_path)
    flags = tmp_path / "runtime" / "flags"
    _write_json(
        flags / "bot_runner.status.json",
        {
            "ts_epoch": 1000.0,
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "with_reconcile": False,
                "symbols": ["B3/USD", "B3/USDC"],
            },
        },
    )
    _write_json(
        flags / "pipeline.status.json",
        {"pid": 101, "loops": 44, "errors": 2, "last_ok": True, "last_reason": "multi_symbol_cycle", "symbols": ["B3/USD", "B3/USDC"]},
    )
    _write_json(
        flags / "intent_executor.status.json",
        {"pid": 102, "loops": 88, "symbols": ["B3/USD", "B3/USDC"]},
    )
    monkeypatch.setattr(
        mod.rbr,
        "load_trading_cfg",
        lambda: {"cfg": True},
    )
    monkeypatch.setattr(
        mod.rbr,
        "desired_state",
        lambda cfg: {
            "mode": "paper",
            "live_enabled": False,
            "with_reconcile": False,
            "venue": "coinbase",
            "symbols": ["B3/USD", "B3/USDC"],
        },
    )
    monkeypatch.setattr(mod.rbr, "desired_services", lambda state: ["pipeline", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor", "executor"])
    monkeypatch.setattr(
        mod,
        "supervisor_status",
        lambda names: {name: {"running": name in {"pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor"}, "pid": 1} for name in names},
    )
    monkeypatch.setattr(
        mod.ai_alert_monitor,
        "load_runtime_status",
        lambda: {
            "pid": 103,
            "status": "idle",
            "pid_alive": True,
            "incidents_written": 7,
            "last_report_stem": "ai_alert_monitor_20260509T174421Z",
            "last_severity": "warn",
            "last_summary": "1 runtime log error burst(s)",
            "reason": "no_new_events",
        },
    )

    out = mod.build_report(now_epoch=1000.0 + 14 * 3600.0)

    assert out["result"] == "IN PROGRESS"
    assert out["counts_for_paper_gate"] is True
    assert out["full_live_path_rehearsal"] is False
    assert out["topology_matches_run_state"] is True
    assert out["symbols"]["aligned"] is True
    assert out["symbols"]["runtime_matches_run_state"] is True
    assert out["pipeline"]["errors"] == 2
    assert out["ai_alert_monitor"]["incidents_written"] == 7
    assert "Section 4.1" in out["section_4_1_entry"]


def test_build_report_threshold_met(monkeypatch, tmp_path):
    mod = _reload_module(monkeypatch, tmp_path)
    flags = tmp_path / "runtime" / "flags"
    _write_json(
        flags / "bot_runner.status.json",
        {
            "ts_epoch": 1000.0,
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "with_reconcile": False,
                "symbols": ["BTC/USD"],
            },
        },
    )
    _write_json(flags / "pipeline.status.json", {"symbols": ["BTC/USD"]})
    _write_json(flags / "intent_executor.status.json", {"symbols": ["BTC/USD"]})
    monkeypatch.setattr(mod.rbr, "load_trading_cfg", lambda: {"cfg": True})
    monkeypatch.setattr(
        mod.rbr,
        "desired_state",
        lambda cfg: {"mode": "paper", "live_enabled": False, "with_reconcile": False, "symbols": ["BTC/USD"]},
    )
    monkeypatch.setattr(mod.rbr, "desired_services", lambda state: ["pipeline", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor", "executor"])
    monkeypatch.setattr(mod, "supervisor_status", lambda names: {name: {"running": True, "pid": 1} for name in names})
    monkeypatch.setattr(mod.ai_alert_monitor, "load_runtime_status", lambda: {"status": "idle", "pid_alive": True, "incidents_written": 0, "reason": "no_new_events"})

    out = mod.build_report(now_epoch=1000.0 + (169 * 3600.0))

    assert out["result"] == "ELAPSED_THRESHOLD_MET"
    assert out["elapsed_hours"] == 169.0
    assert out["remaining_hours"] == 0.0


def test_format_text_includes_copy_paste_section_entry(monkeypatch, tmp_path):
    mod = _reload_module(monkeypatch, tmp_path)
    flags = tmp_path / "runtime" / "flags"
    _write_json(
        flags / "bot_runner.status.json",
        {
            "ts_epoch": 1000.0,
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "with_reconcile": False,
                "symbols": ["BTC/USD"],
            },
        },
    )
    _write_json(flags / "pipeline.status.json", {"symbols": ["BTC/USD"], "loops": 10, "errors": 0, "last_ok": True, "last_reason": "multi_symbol_cycle"})
    _write_json(flags / "intent_executor.status.json", {"symbols": ["BTC/USD"], "loops": 20})
    monkeypatch.setattr(mod.rbr, "load_trading_cfg", lambda: {"cfg": True})
    monkeypatch.setattr(
        mod.rbr,
        "desired_state",
        lambda cfg: {"mode": "paper", "live_enabled": False, "with_reconcile": False, "symbols": ["BTC/USD"]},
    )
    monkeypatch.setattr(mod.rbr, "desired_services", lambda state: ["pipeline", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor", "executor"])
    monkeypatch.setattr(
        mod,
        "supervisor_status",
        lambda names: {name: {"running": name in {"pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor"}, "pid": 1} for name in names},
    )
    monkeypatch.setattr(mod.ai_alert_monitor, "load_runtime_status", lambda: {"status": "idle", "pid_alive": True, "incidents_written": 0, "reason": "no_new_events"})

    out = mod.build_report(now_epoch=1000.0 + 3600.0)
    txt = mod.format_text(out)

    assert "Counts for paper gate: True" in txt
    assert "Section 4.1 — Minimum paper trading duration" in txt
    assert "Status: not eligible for PASS until the 7-day continuous window completes." in txt


def test_build_report_flags_current_desired_symbol_drift(monkeypatch, tmp_path):
    mod = _reload_module(monkeypatch, tmp_path)
    flags = tmp_path / "runtime" / "flags"
    _write_json(
        flags / "bot_runner.status.json",
        {
            "ts_epoch": 1000.0,
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "with_reconcile": False,
                "symbols": ["B3/USD", "B3/USDC"],
            },
        },
    )
    _write_json(flags / "pipeline.status.json", {"symbols": ["B3/USD", "B3/USDC"]})
    _write_json(flags / "intent_executor.status.json", {"symbols": ["B3/USD", "B3/USDC"]})
    monkeypatch.setattr(mod.rbr, "load_trading_cfg", lambda: {"cfg": True})
    monkeypatch.setattr(
        mod.rbr,
        "desired_state",
        lambda cfg: {"mode": "paper", "live_enabled": False, "with_reconcile": False, "symbols": ["BILL/USD", "BILL/USDC"]},
    )
    monkeypatch.setattr(mod.rbr, "desired_services", lambda state: ["pipeline", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor", "executor"])
    monkeypatch.setattr(
        mod,
        "supervisor_status",
        lambda names: {name: {"running": name in {"pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor"}, "pid": 1} for name in names},
    )
    monkeypatch.setattr(mod.ai_alert_monitor, "load_runtime_status", lambda: {"status": "idle", "pid_alive": True, "incidents_written": 0, "reason": "no_new_events"})

    out = mod.build_report(now_epoch=1000.0 + 3600.0)

    assert out["counts_for_paper_gate"] is True
    assert out["symbols"]["runtime_matches_run_state"] is True
    assert out["symbols"]["runtime_matches_current_desired_state"] is False
    assert out["current_desired_state"]["symbols"] == ["BILL/USD", "BILL/USDC"]


def test_build_report_does_not_count_safe_idle_service_as_valid_topology(monkeypatch, tmp_path):
    mod = _reload_module(monkeypatch, tmp_path)
    flags = tmp_path / "runtime" / "flags"
    _write_json(
        flags / "bot_runner.status.json",
        {
            "ts_epoch": 1000.0,
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "with_reconcile": False,
                "symbols": ["B3/USD", "B3/USDC"],
            },
        },
    )
    _write_json(flags / "pipeline.status.json", {"symbols": ["B3/USD", "B3/USDC"], "status": "safe_idle"})
    _write_json(flags / "intent_executor.status.json", {"symbols": ["B3/USD", "B3/USDC"]})
    monkeypatch.setattr(mod.rbr, "load_trading_cfg", lambda: {"cfg": True})
    monkeypatch.setattr(
        mod.rbr,
        "desired_state",
        lambda cfg: {"mode": "paper", "live_enabled": False, "with_reconcile": False, "symbols": ["B3/USD", "B3/USDC"]},
    )
    monkeypatch.setattr(mod.rbr, "desired_services", lambda state: ["pipeline", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor", "executor"])
    monkeypatch.setattr(
        mod,
        "supervisor_status",
        lambda names: {
            name: (
                {"running": True, "pid": 1, "status": "safe_idle", "healthy": False}
                if name == "pipeline"
                else {"running": name in {"executor", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor"}, "pid": 1, "status": "running", "healthy": True}
            )
            for name in names
        },
    )
    monkeypatch.setattr(mod.ai_alert_monitor, "load_runtime_status", lambda: {"status": "idle", "pid_alive": True, "incidents_written": 0, "reason": "no_new_events"})

    out = mod.build_report(now_epoch=1000.0 + 3600.0)

    assert out["counts_for_paper_gate"] is False
    assert out["topology_matches_run_state"] is False
