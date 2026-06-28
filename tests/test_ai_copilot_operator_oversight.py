from __future__ import annotations

import json

from services.ai_copilot import operator_oversight as svc


def _gate_payload() -> dict:
    return {
        "ready": False,
        "machine_ready": False,
        "manual_review_required": True,
        "strategy_id": "es_daily_trend_v1",
        "stage": "paper",
        "gates": [
            {
                "label": "10+ completed round trips",
                "passed": False,
                "detail": "2/10, 8 remaining",
                "hint": "continue running",
            }
        ],
        "manual_review": {
            "outstanding_items": [
                {
                    "id": "win_rate",
                    "label": "Win rate vs backtest",
                    "status": "machine_blocking",
                    "reason": "outside tolerance",
                }
            ]
        },
        "paper_history": {
            "source": "jsonl_provenance+trade_journal_sqlite",
            "fills": 4,
            "closed_trades": 2,
            "all_history_fills": 18,
            "all_history_closed_trades": 9,
            "latest_fill_ts": "2026-06-24T00:04:01+00:00",
            "qualification": {
                "evidence_fills": 14,
                "qualified_evidence_fills": 4,
                "completed_evidence_round_trips": 2,
                "unqualified_evidence_fills": 9,
                "incomplete_qualified_evidence_fills": 1,
                "latest_completed_qualified_round_trip_close_ts": "2026-06-24T00:04:01+00:00",
            },
        },
    }


def _monitor_payload(**overrides) -> dict:
    payload = {
        "ok": True,
        "has_status": True,
        "status": "stopped",
        "reason": "stop_requested",
        "pid_alive": False,
        "campaign_status": "idle",
        "campaign_reason": "waiting_for_next_day",
        "recommendation": "continue",
        "recommendation_reason": "monitor_idle",
        "strategy_label": "es_daily_trend_v1",
        "symbol": "BTC/USDT",
        "summary_text": "Monitor summary",
        "watches": [
            {"name": "next_fill", "trigger": "new_fill", "active": True},
        ],
        "recent_watch_reports": [],
    }
    payload.update(overrides)
    return payload


def test_operator_oversight_reports_missing_monitor_status(monkeypatch) -> None:
    monkeypatch.setattr(
        svc,
        "load_paper_sim_monitor_status",
        lambda: {"ok": True, "has_status": False, "status": "not_started"},
    )
    monkeypatch.setattr(svc, "_gate_payload", _gate_payload)

    report = svc.build_operator_oversight_report()

    assert report["status"] == "insufficient_status"
    assert report["read_only"] is True
    assert report["machine_facts"]["monitor"]["has_status"] is False
    assert report["action_items"][0]["id"] == "restore_monitor_status"
    assert report["safety"]["orders_routed"] is False
    assert report["safety"]["promotion_gate_mutated"] is False


def test_operator_oversight_reports_missing_watch_reports(monkeypatch) -> None:
    monkeypatch.setattr(svc, "load_paper_sim_monitor_status", lambda: _monitor_payload())
    monkeypatch.setattr(svc, "_gate_payload", _gate_payload)

    report = svc.build_operator_oversight_report()

    assert report["watch_report_status"] == "no_recent_watch_reports"
    assert any(item["id"] == "no_recent_watch_reports" for item in report["action_items"])
    assert report["status"] == "paper_gate_blocked"


def test_operator_oversight_turns_investigate_watch_into_action(monkeypatch) -> None:
    monkeypatch.setattr(
        svc,
        "load_paper_sim_monitor_status",
        lambda: _monitor_payload(
            recent_watch_reports=[
                {
                    "watch_name": "investigate",
                    "trigger": "recommendation_investigate",
                    "severity": "warn",
                    "summary": "Watch requested investigation.",
                    "generated_at": "2026-06-28T00:01:36+00:00",
                }
            ]
        ),
    )
    monkeypatch.setattr(svc, "_gate_payload", _gate_payload)

    report = svc.build_operator_oversight_report()

    assert report["status"] == "investigate"
    assert report["watch_report_status"] == "available"
    assert any(item["id"] == "investigate_watch_report" for item in report["action_items"])


def test_operator_oversight_surfaces_paper_gate_blockers(monkeypatch) -> None:
    monkeypatch.setattr(svc, "load_paper_sim_monitor_status", lambda: _monitor_payload())
    monkeypatch.setattr(svc, "_gate_payload", _gate_payload)

    report = svc.build_operator_oversight_report()

    blockers = report["machine_facts"]["paper_gate"]["blockers"]
    assert blockers[0]["label"] == "10+ completed round trips"
    assert blockers[0]["detail"] == "2/10, 8 remaining"
    assert any(item["id"] == "paper_gate_blocker" for item in report["action_items"])


def test_operator_oversight_ai_provider_absence_degrades_to_machine_summary(monkeypatch) -> None:
    monkeypatch.setattr(svc, "load_paper_sim_monitor_status", lambda: _monitor_payload())
    monkeypatch.setattr(svc, "_gate_payload", _gate_payload)
    monkeypatch.setattr(
        svc,
        "call_llm",
        lambda **_kwargs: {"ok": False, "error": "Missing Anthropic API key"},
    )

    report = svc.build_operator_oversight_report(use_ai=True)

    assert report["ai_summary"]["status"] == "machine_only"
    assert report["ai_summary"]["reason"] == "Missing Anthropic API key"
    assert report["ai_summary"]["text"] == report["machine_summary"]


def test_operator_oversight_writes_json_and_markdown(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(svc, "load_paper_sim_monitor_status", lambda: _monitor_payload())
    monkeypatch.setattr(svc, "_gate_payload", _gate_payload)

    report = svc.build_operator_oversight_report()
    paths = svc.write_operator_oversight_report(report)

    latest_json = tmp_path / "runtime" / "ai_reports" / "ai_operator_oversight.latest.json"
    latest_md = tmp_path / "runtime" / "ai_reports" / "ai_operator_oversight.latest.md"
    assert paths["latest_json"] == str(latest_json)
    assert paths["latest_markdown"] == str(latest_md)
    assert json.loads(latest_json.read_text(encoding="utf-8"))["report_type"] == "ai_operator_oversight"
    assert "AI Operator Oversight Report" in latest_md.read_text(encoding="utf-8")


def test_operator_oversight_keeps_candidate_advisor_disabled(monkeypatch) -> None:
    monkeypatch.setattr(svc, "load_paper_sim_monitor_status", lambda: _monitor_payload())
    monkeypatch.setattr(svc, "_gate_payload", _gate_payload)

    report = svc.build_operator_oversight_report()

    assert report["machine_facts"]["candidate_advisor"]["enabled"] is False
    assert report["safety"]["candidate_advisor_enabled"] is False
