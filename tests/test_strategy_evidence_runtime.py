from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dashboard.services import strategy_evidence_runtime as runtime


def test_load_paper_strategy_evidence_runtime_flags_tick_freshness_blocker(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.analytics.paper_strategy_evidence_service.load_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "running",
            "ts": "2026-03-26T12:00:00Z",
            "completed_strategies": 0,
            "total_strategies": 2,
            "summary_text": (
                "Paper evidence collector is running on ema_cross (0/2 complete). "
                "Strategy runner is waiting for fresh market ticks for ema_cross; start the tick publisher."
            ),
        },
    )

    payload = runtime.load_paper_strategy_evidence_runtime()

    assert payload["alert_tone"] == "warning"
    assert "waiting for fresh market ticks" in payload["alert_text"]


def test_load_paper_strategy_evidence_runtime_has_no_alert_for_normal_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.analytics.paper_strategy_evidence_service.load_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "completed",
            "ts": "2026-03-26T12:00:00Z",
            "completed_strategies": 2,
            "total_strategies": 2,
            "summary_text": "Paper evidence collector completed.",
        },
    )

    payload = runtime.load_paper_strategy_evidence_runtime()

    assert payload["alert_tone"] == ""
    assert payload["alert_text"] == ""


def test_load_paper_sim_monitor_runtime_flags_investigate(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.analytics.paper_sim_monitor.load_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "stopped",
            "ts": "2026-03-26T12:00:00Z",
            "recommendation": "investigate",
            "strategy_label": "es_daily_trend_v1",
            "symbol": "BTC/USDT",
            "fills_observed": 0,
            "round_trips_observed": 0,
            "summary_text": "Paper sim monitor sees es_daily_trend_v1 on BTC/USDT with campaign completed; recommendation=investigate.",
        },
    )

    payload = runtime.load_paper_sim_monitor_runtime()

    assert payload["alert_tone"] == "warning"
    assert "recommendation=investigate" in payload["alert_text"]
    assert payload["freshness"] in {"Fresh", "Aging", "Stale", "Unknown"}


def test_strategy_evidence_runtime_imports_standalone() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from dashboard.services.strategy_evidence_runtime import "
                "load_paper_sim_monitor_runtime; "
                "print(bool(load_paper_sim_monitor_runtime))"
            ),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "True"
