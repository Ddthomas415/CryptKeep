from __future__ import annotations


def test_research_command_status_reports_all_commands_on_current_repo() -> None:
    from services.analytics.research_command_status import build_research_command_status

    out = build_research_command_status()

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["not_research_execution"] is True
    assert out["not_campaign_evidence"] is True
    assert out["not_promotion_evidence"] is True
    assert out["not_execution_input"] is True
    assert out["command_count"] >= 18
    assert out["summary"]["not_wired"] == 0
    assert out["summary"]["by_lane"]["funding"] >= 7
    assert out["summary"]["by_lane"]["price_action"] >= 5
    assert out["summary"]["by_input_class"]["artifact_input"] >= 5
    assert out["makefile_sha256"]
    assert out["script_index_sha256"]
    rows = {row["command_id"]: row for row in out["commands"]}
    assert rows["research_command_status"]["script_index_exists"] is True
    assert rows["research_command_status"]["make_target"] is None
    assert rows["funding_threshold_pipeline"]["make_target"] == "funding-threshold-research-pipeline"


def test_research_command_status_fails_closed_on_wiring_drift(tmp_path) -> None:
    from services.analytics.research_command_status import build_research_command_status

    (tmp_path / "scripts" / "research").mkdir(parents=True)
    (tmp_path / "scripts" / "SCRIPTS.md").write_text("", encoding="utf-8")
    (tmp_path / "Makefile").write_text("", encoding="utf-8")

    out = build_research_command_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["summary"]["wired"] == 0
    assert any("script_missing" in row["reasons"] for row in out["commands"])
    assert any("script_index_missing" in row["reasons"] for row in out["commands"])
    assert any("make_target_missing" in row["reasons"] for row in out["commands"])


def test_report_research_command_status_cli(monkeypatch, capsys) -> None:
    from scripts.research import report_research_command_status as script

    monkeypatch.setattr(
        script,
        "build_research_command_status",
        lambda repo_root=None: {
            "ok": True,
            "command_count": 2,
            "summary": {
                "wired": 2,
                "not_wired": 0,
                "by_lane": {"funding": 1, "status": 1},
                "by_input_class": {"state_input": 1, "none": 1},
            },
            "commands": [
                {
                    "command_id": "funding_threshold_pipeline",
                    "wiring_ok": True,
                    "lane": "funding",
                    "input_class": "state_input",
                    "make_target": "funding-threshold-research-pipeline",
                    "reasons": [],
                }
            ],
        },
    )

    assert script.main([]) == 0
    out = capsys.readouterr().out
    assert "Research Command Status" in out
    assert "wired=2" in out
    assert "funding_threshold_pipeline" in out
