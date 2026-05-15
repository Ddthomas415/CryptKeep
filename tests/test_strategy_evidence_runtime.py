from __future__ import annotations

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


def test_load_paper_sim_monitor_runtime_exposes_watch_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.analytics.paper_sim_monitor.load_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "running",
            "ts": "2026-05-15T10:00:00Z",
            "recommendation": "continue",
            "watches": [{"name": "next_fill", "trigger": "new_fill"}],
            "recent_watch_reports": [
                {
                    "watch_name": "next_fill",
                    "trigger": "new_fill",
                    "severity": "info",
                    "summary": "Watch `next_fill` fired.",
                    "generated_at": "2026-05-15T10:01:00Z",
                }
            ],
        },
    )

    payload = runtime.load_paper_sim_monitor_runtime()

    assert payload["watch_count"] == 1
    assert payload["recent_report_count"] == 1
    assert payload["registered_watch_names"] == ["next_fill"]
    assert payload["last_watch_report"]["watch_name"] == "next_fill"
    assert payload["alert_tone"] == ""
    assert payload["alert_text"] == ""
