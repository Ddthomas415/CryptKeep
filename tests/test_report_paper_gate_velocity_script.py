from __future__ import annotations

import json


def test_report_paper_gate_velocity_evidence_dest_writes_artifact(monkeypatch, tmp_path, capsys) -> None:
    from scripts import report_paper_gate_velocity as script

    monkeypatch.setattr(
        script,
        "build_paper_gate_velocity_report",
        lambda: {
            "ok": True,
            "read_only": True,
            "report_type": "paper_gate_velocity",
            "strategy_id": "es_daily_trend_v1",
            "target_strategy": "sma_200_trend",
            "policy_id": "slow_daily_single_symbol_v1",
            "policy_valid": True,
            "round_trips": {"qualified": 3, "required": 5, "remaining": 2},
            "qualified_bars": {
                "enabled": True,
                "recorded": 47,
                "required": 60,
                "remaining": 13,
            },
            "velocity": {"status": "projected"},
            "qualified_bar_velocity": {"status": "projected"},
            "overall_velocity": {"status": "projected"},
            "findings": [],
            "summary_text": "paper gate status",
        },
    )

    assert script.main(["--json", "--evidence-dest", str(tmp_path)]) == 0

    payload = json.loads(capsys.readouterr().out)
    latest = tmp_path / "paper_gate_velocity.latest.json"
    assert latest.exists()
    assert payload["artifact_paths"]["latest_json"] == str(latest)
    assert json.loads(latest.read_text(encoding="utf-8"))["report_type"] == "paper_gate_velocity"
