from __future__ import annotations

import json

from scripts import report_supervised_soak_status as script


def test_build_report_is_read_only_and_summarizes_campaigns(monkeypatch) -> None:
    monkeypatch.setattr(script, "load_campaign_specs", lambda *args, **kwargs: ("spec",))

    seen: dict[str, object] = {}

    def _manage(specs, *, restore, selected_names):
        seen["specs"] = specs
        seen["restore"] = restore
        seen["selected_names"] = selected_names
        return {
            "ok": True,
            "all_running": True,
            "campaign_count": 1,
            "running_count": 1,
            "campaigns": [
                {
                    "name": "es_daily_trend_v1",
                    "ok": True,
                    "running": True,
                    "status": "idle",
                    "reason": "waiting_for_next_day",
                    "strategy": "sma_200_trend",
                    "session_strategy_id": "es_daily_trend_v1",
                    "last_completed_day": "2026-06-19",
                    "pid": 123,
                    "collector": {
                        "summary_text": "waiting",
                        "last_result": {
                            "results": [
                                {
                                    "latest_fill_ts": "2026-06-18T00:00:00+00:00",
                                    "fills_total": 16,
                                    "closed_trades_total": 8,
                                    "net_realized_pnl_total": 33.8,
                                    "signal_action": "hold",
                                    "runner_status": "stopped",
                                }
                            ]
                        },
                    },
                }
            ],
        }

    monkeypatch.setattr(script, "manage_campaigns", _manage)

    import scripts.check_promotion_gates as gates

    monkeypatch.setattr(
        gates,
        "run_check",
        lambda stage_override=None: {
            "strategy_id": "es_daily_trend_v1",
            "stage": stage_override or "paper",
            "current_stage": "paper",
            "ready": False,
            "machine_ready": False,
            "manual_review_required": True,
            "summary": {"pass": 7, "fail": 1, "unknown": 1, "total": 9},
            "gates": [
                {"label": "30 calendar days of operation", "passed": True, "detail": "45/30 days"},
                {"label": "10+ completed round trips", "passed": False, "detail": "1/10"},
                {"label": "Expectancy within tolerable range of backtest", "passed": None, "detail": "insufficient"},
            ],
            "evidence_writer": {
                "evidence_writer_status": "refusing",
                "evidence_write_failures_total": 3,
                "evidence_write_failures_consecutive": 3,
                "last_evidence_write_error_type": "OSError",
                "threshold": 3,
            },
            "paper_history": {
                "source": "jsonl_provenance+trade_journal_sqlite",
                "fills": 4,
                "closed_trades": 2,
                "latest_fill_ts": "2026-06-24T00:04:01+00:00",
                "all_history": {
                    "fills": 18,
                    "closed_trades": 9,
                    "latest_fill_ts": "2026-06-24T00:04:01+00:00",
                },
                "qualification": {
                    "evidence_fills": 14,
                    "qualified_evidence_fills": 4,
                    "provenance_qualified_evidence_fills": 5,
                    "completed_evidence_round_trips": 2,
                    "incomplete_qualified_evidence_fills": 1,
                    "unqualified_evidence_fills": 9,
                    "latest_completed_qualified_round_trip_close_ts": "2026-06-24T00:04:01+00:00",
                },
            },
            "manual_review": {
                "summary": "manual review required",
                "outstanding_items": [
                    {
                        "id": "win_rate",
                        "label": "Win rate",
                        "status": "machine_blocking",
                        "reason": "outside tolerance",
                    }
                ],
            },
        },
    )

    out = script.build_report(selected_campaigns=["es_daily_trend_v1"])

    assert seen == {
        "specs": ("spec",),
        "restore": False,
        "selected_names": ["es_daily_trend_v1"],
    }
    assert out["read_only"] is True
    assert out["all_running"] is True
    assert out["campaigns"][0]["closed_trades_total"] == 8
    assert out["gate"]["round_trips"]["detail"] == "1/10"
    assert out["gate"]["manual_review_required"] is True
    assert out["gate"]["evidence_writer"]["evidence_writer_status"] == "refusing"
    assert out["gate"]["paper_history"]["closed_trades"] == 2
    assert out["gate"]["paper_history"]["all_history_closed_trades"] == 9
    assert out["gate"]["paper_history"]["qualification"] == {
        "evidence_fills": 14,
        "qualified_evidence_fills": 4,
        "provenance_qualified_evidence_fills": 5,
        "completed_evidence_round_trips": 2,
        "incomplete_qualified_evidence_fills": 1,
        "unqualified_evidence_fills": 9,
        "first_provenance_qualified_fill_ts": None,
        "latest_provenance_qualified_fill_ts": None,
        "first_completed_qualified_round_trip_close_ts": None,
        "latest_completed_qualified_round_trip_close_ts": "2026-06-24T00:04:01+00:00",
    }
    assert out["recommendations"] == [
        "investigate_evidence_writer",
        "manual_strategy_review_required",
        "continue_paper_observation",
    ]


def test_main_outputs_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_report",
        lambda **kwargs: {
            "ok": True,
            "read_only": True,
            "campaigns": [],
            "gate": {},
            "recommendations": ["ready_for_operator_gate_review"],
        },
    )

    assert script.main(["--json", "--campaign", "ema_cross_default"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["read_only"] is True
    assert out["recommendations"] == ["ready_for_operator_gate_review"]


def test_main_strict_returns_one_when_report_not_ok(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_report",
        lambda **kwargs: {
            "ok": False,
            "read_only": True,
            "campaigns": [],
            "gate": {},
            "recommendations": ["investigate_campaign_processes"],
        },
    )

    assert script.main(["--strict", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
