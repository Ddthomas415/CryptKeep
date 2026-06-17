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


def test_load_paper_strategy_evidence_runtime_warns_on_watch_seed_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.analytics.paper_strategy_evidence_service.load_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "running",
            "ts": "2026-05-15T12:00:00Z",
            "completed_strategies": 0,
            "total_strategies": 1,
            "summary_text": "Paper evidence collector is running on sma_200_trend (0/1 complete).",
            "paper_sim_monitor_watch_seed": {
                "ok": False,
                "reason": "paper_sim_watch_register_failed:next_fill:write_failed",
                "watch_count": 1,
            },
        },
    )

    payload = runtime.load_paper_strategy_evidence_runtime()

    assert payload["paper_sim_watch_seed_ok"] is False
    assert payload["paper_sim_watch_seed_reason"] == "paper_sim_watch_register_failed:next_fill:write_failed"
    assert payload["paper_sim_watch_seed_count"] == 1
    assert payload["alert_tone"] == "warning"
    assert "default watch registration degraded" in payload["alert_text"].lower()


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


def test_load_paper_sim_monitor_runtime_exposes_watch_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.analytics.paper_sim_monitor.load_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "running",
            "ts": "2026-05-15T10:00:00Z",
            "desktop_notify": True,
            "recommendation": "continue",
            "promotion_progress": {
                "applicable": True,
                "thresholds_ready": False,
                "blocking_thresholds": [{"label": "10+ completed round trips"}],
                "summary_text": "Promotion threshold progress: 22/30 days recorded (8 remaining), 7/10 round trips recorded (3 remaining).",
            },
            "watches": [{"name": "next_fill", "trigger": "new_fill"}],
            "recent_watch_reports": [
                {
                    "watch_name": "next_fill",
                    "trigger": "new_fill",
                    "severity": "info",
                    "summary": "Watch `next_fill` fired.",
                    "generated_at": "2026-05-15T10:01:00Z",
                    "desktop_notification": {"attempted": True, "sent": True, "reason": "notified"},
                }
            ],
        },
    )

    payload = runtime.load_paper_sim_monitor_runtime()

    assert payload["watch_count"] == 1
    assert payload["recent_report_count"] == 1
    assert payload["registered_watch_names"] == ["next_fill"]
    assert payload["last_watch_report"]["watch_name"] == "next_fill"
    assert payload["promotion_thresholds_applicable"] is True
    assert payload["promotion_thresholds_ready"] is False
    assert payload["promotion_blocking_threshold_count"] == 1
    assert "7/10 round trips" in payload["promotion_progress_summary"]
    assert payload["desktop_notify_enabled"] is True
    assert payload["notification_status"] == "sent"
    assert payload["notification_reason"] == "notified"
    assert payload["alert_tone"] == ""
    assert payload["alert_text"] == ""


def test_load_paper_sim_monitor_runtime_marks_unconfigured_promotion_policy(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "services.analytics.paper_sim_monitor.load_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "idle",
            "ts": "2026-06-12T00:19:43Z",
            "promotion_progress": {
                "applicable": False,
                "status": "not_configured",
                "thresholds_ready": False,
                "blocking_thresholds": [],
                "summary_text": (
                    "Promotion thresholds are not configured for breakout_default; "
                    "campaign trade metrics are informational."
                ),
            },
        },
    )

    payload = runtime.load_paper_sim_monitor_runtime()

    assert payload["promotion_thresholds_applicable"] is False
    assert payload["promotion_thresholds_ready"] is False
    assert payload["promotion_blocking_threshold_count"] == 0
    assert "not configured for breakout_default" in payload["promotion_progress_summary"]


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
