from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import services.ai_copilot.operator_briefing as briefing


ROOT = Path(__file__).resolve().parents[1]


def _minimal_status() -> dict:
    return {
        "ok": True,
        "summary": {"operator_proof_actions_required": 0},
        "reports": {
            "paper_campaign_status": {
                "ok": True,
                "all_running": True,
                "running_count": 2,
                "campaign_count": 2,
                "campaigns": [
                    {
                        "name": "es_daily_trend_v1",
                        "status": "idle",
                        "reason": "waiting_next_utc_day",
                        "strategy": "es_daily_trend",
                        "session_strategy_id": "es_daily_trend_v1",
                        "closed_trades_total": 10,
                        "fills_total": 20,
                    }
                ],
            }
        },
    }


def _idle_campaign_status() -> dict:
    return {
        "ok": True,
        "all_running": False,
        "running_count": 0,
        "campaign_count": 2,
        "campaigns": [
            {
                "name": "es_daily_trend_v1",
                "status": "idle",
                "reason": "waiting_for_next_day",
                "running": False,
                "ok": True,
                "strategy": "sma_200_trend",
                "session_strategy_id": "es_daily_trend_v1",
                "collector": {"last_result": {"results": [{"closed_trades_total": 10, "fills_total": 20}]}},
            },
            {
                "name": "breakout_default",
                "status": "idle",
                "reason": "waiting_for_next_day",
                "running": False,
                "ok": True,
                "strategy": "breakout_donchian",
                "session_strategy_id": "breakout_default",
                "collector": {"last_result": {"results": [{"closed_trades_total": 11, "fills_total": 23}]}},
            },
        ],
    }


def _minimal_next_actions() -> dict:
    return {
        "ok": True,
        "action_count_total": 1,
        "action_count_available": 1,
        "action_count_returned": 1,
        "summary": {"available_by_lane": {"operator_proof": 1}},
        "actions": [
            {
                "lane": "operator_proof",
                "source": "paper_gate",
                "blocking_reason": "passive_operator_evidence",
                "next_action": "record the next accepted proof artifact",
            }
        ],
    }


def _minimal_gate() -> dict:
    return {
        "ok": True,
        "round_trips": {"qualified": 3, "required": 5, "remaining": 2, "excluded_all_history": 4},
        "qualified_bars": {"enabled": True, "recorded": 61, "required": 60, "remaining": 0, "ready": True},
        "velocity": {"status": "projected", "estimated_days_remaining": 20},
        "overall_velocity": {
            "status": "projected",
            "blocking_threshold": "round_trips",
            "estimated_completion_ts": "2026-09-12T00:00:00+00:00",
        },
        "findings": [],
    }


def _minimal_cost() -> dict:
    return {
        "overall": "warning",
        "round_trip_bps": 25.0,
        "policy_floor_bps": 5.0,
        "checks": [
            {
                "name": "backtest_costs_independent",
                "status": "warning",
                "detail": "backtest path is independently sourced",
            }
        ],
    }


def test_operator_briefing_is_read_only_advisory(monkeypatch, tmp_path):
    monkeypatch.setattr(briefing, "build_operator_status_bundle", lambda **_: _minimal_status())
    monkeypatch.setattr(briefing, "build_operator_next_actions", lambda **_: _minimal_next_actions())
    captured: dict[str, object] = {}

    def _campaign_status(**kwargs: object) -> dict:
        captured.update(kwargs)
        return _minimal_status()["reports"]["paper_campaign_status"]

    monkeypatch.setattr(briefing, "build_paper_campaign_status_report", _campaign_status)
    monkeypatch.setattr(briefing, "build_paper_gate_velocity_report", lambda: _minimal_gate())
    monkeypatch.setattr(briefing, "check_cost_assumptions", lambda: _minimal_cost())

    payload = briefing.build_operator_briefing(repo_root=tmp_path)

    assert payload["report_type"] == "operator_briefing"
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["capital_authority"] == "none"
    assert payload["does_not_mutate_state"] is True
    assert payload["does_not_run_campaigns"] is True
    assert payload["does_not_start_or_stop_campaigns"] is True
    assert payload["does_not_fetch_market_data"] is True
    assert payload["does_not_change_config"] is True
    assert payload["does_not_promote_strategies"] is True
    assert payload["summaries"]["campaigns"]["running_count"] == 2
    assert payload["summaries"]["paper_gate"]["round_trips"]["remaining"] == 2
    assert any(row["id"] == "cost_assumption_attention" for row in payload["recommendations"])
    assert str(captured["config_path"]).endswith("configs/paper_evidence_campaigns.laptop.json")


def test_operator_briefing_survives_source_failure(monkeypatch, tmp_path):
    def _broken_status(**_: object) -> dict:
        raise RuntimeError("boom")

    monkeypatch.setattr(briefing, "build_operator_status_bundle", _broken_status)
    monkeypatch.setattr(briefing, "build_operator_next_actions", lambda **_: _minimal_next_actions())
    monkeypatch.setattr(
        briefing,
        "build_paper_campaign_status_report",
        lambda **_: _minimal_status()["reports"]["paper_campaign_status"],
    )
    monkeypatch.setattr(briefing, "build_paper_gate_velocity_report", lambda: _minimal_gate())
    monkeypatch.setattr(briefing, "check_cost_assumptions", lambda: _minimal_cost())

    payload = briefing.build_operator_briefing(repo_root=tmp_path)

    assert payload["ok"] is False
    assert payload["reason"] == "source_failed"
    assert payload["source_status"]["operator_status"]["ok"] is False
    assert payload["source_status"]["operator_status"]["error_type"] == "RuntimeError"
    assert payload["recommendations"]


def test_operator_briefing_does_not_recommend_restore_for_scheduled_daily_idle(monkeypatch, tmp_path):
    monkeypatch.setattr(briefing, "build_operator_status_bundle", lambda **_: _minimal_status())
    monkeypatch.setattr(briefing, "build_operator_next_actions", lambda **_: _minimal_next_actions())
    monkeypatch.setattr(briefing, "build_paper_campaign_status_report", lambda **_: _idle_campaign_status())
    monkeypatch.setattr(briefing, "build_paper_gate_velocity_report", lambda: _minimal_gate())
    monkeypatch.setattr(briefing, "check_cost_assumptions", lambda: _minimal_cost())

    payload = briefing.build_operator_briefing(repo_root=tmp_path)

    assert payload["summaries"]["campaigns"]["all_running"] is False
    assert payload["summaries"]["campaigns"]["attention_required"] is False
    assert payload["summaries"]["campaigns"]["attention_count"] == 0
    assert not any(row["id"] == "campaign_process_attention" for row in payload["recommendations"])


def test_operator_briefing_cli_json_executes():
    proc = subprocess.run(
        [sys.executable, "scripts/report_operator_briefing.py", "--json", "--max-actions", "2"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert proc.returncode in {0, 1}
    payload = json.loads(proc.stdout)
    assert payload["report_type"] == "operator_briefing"
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["capital_authority"] == "none"
    assert payload["does_not_mutate_state"] is True


def test_operator_briefing_writes_json_and_markdown_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr(briefing, "build_operator_status_bundle", lambda **_: _minimal_status())
    monkeypatch.setattr(briefing, "build_operator_next_actions", lambda **_: _minimal_next_actions())
    monkeypatch.setattr(
        briefing,
        "build_paper_campaign_status_report",
        lambda **_: _minimal_status()["reports"]["paper_campaign_status"],
    )
    monkeypatch.setattr(briefing, "build_paper_gate_velocity_report", lambda: _minimal_gate())
    monkeypatch.setattr(briefing, "check_cost_assumptions", lambda: _minimal_cost())
    monkeypatch.setattr(
        briefing,
        "record_ai_copilot_report_write",
        lambda **_: {"ok": True, "event_id": "evt-1", "path": str(tmp_path / "events.jsonl")},
    )

    payload = briefing.build_operator_briefing(repo_root=tmp_path)
    paths = briefing.write_operator_briefing_artifact(payload, evidence_dest=tmp_path / "briefings")

    latest_json = Path(paths["latest_json"])
    latest_markdown = Path(paths["latest_markdown"])
    assert latest_json.is_file()
    assert latest_markdown.is_file()
    assert Path(paths["dated_json"]).is_file()
    assert Path(paths["dated_markdown"]).is_file()
    saved = json.loads(latest_json.read_text(encoding="utf-8"))
    assert saved["report_type"] == "operator_briefing"
    assert saved["capital_authority"] == "none"
    markdown = latest_markdown.read_text(encoding="utf-8")
    assert "# Operator Briefing" in markdown
    assert "This artifact is advisory." in markdown
    assert paths["operator_event"]["ok"] is True


def test_operator_briefing_cli_record_mode_names_artifact_mutation(tmp_path):
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/report_operator_briefing.py",
            "--json",
            "--max-actions",
            "1",
            "--evidence-dest",
            str(tmp_path / "briefings"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert proc.returncode in {0, 1}
    payload = json.loads(proc.stdout)
    assert payload["artifact_write_requested"] is True
    assert payload["does_not_mutate_state"] is False
    assert payload["does_not_mutate_runtime_state"] is True
    assert payload["mutates_only_operator_briefing_artifacts"] is True
    assert Path(payload["artifact_paths"]["latest_json"]).is_file()
    saved = json.loads(Path(payload["artifact_paths"]["latest_json"]).read_text(encoding="utf-8"))
    assert saved["artifact_write_requested"] is True
    assert saved["does_not_mutate_state"] is False
    assert saved["does_not_mutate_runtime_state"] is True
