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
    assert rows["research_command_status"]["make_target"] == "research-command-status"
    assert rows["research_command_status"]["action_required"] is False
    assert rows["research_command_status"]["blocking_reason"] is None
    assert rows["research_command_status"]["next_action"] == "none"
    assert rows["funding_threshold_pipeline"]["make_target"] == "funding-threshold-research-pipeline"


def test_research_command_status_filters_by_lane_and_input_class() -> None:
    from services.analytics.research_command_status import build_research_command_status

    out = build_research_command_status(lane="funding", input_class="artifact_input")

    assert out["lane_filter"] == "funding"
    assert out["input_class_filter"] == "artifact_input"
    assert out["command_count"] >= 4
    assert out["source_command_count"] >= out["command_count"]
    assert out["summary"]["by_lane"] == {"funding": out["command_count"]}
    assert out["summary"]["by_input_class"] == {"artifact_input": out["command_count"]}
    assert out["summary"]["source_by_lane"]["price_action"] >= 5
    assert all(row["lane"] == "funding" for row in out["commands"])
    assert all(row["input_class"] == "artifact_input" for row in out["commands"])


def test_research_command_status_filters_by_command_id() -> None:
    from services.analytics.research_command_status import build_research_command_status

    out = build_research_command_status(command_id="funding_threshold_pipeline")

    assert out["ok"] is True
    assert out["command_id_filter"] == "funding_threshold_pipeline"
    assert out["command_count"] == 1
    assert out["source_command_count"] >= out["command_count"]
    assert "funding_threshold_pipeline" in out["available_command_ids"]
    assert out["commands"][0]["command_id"] == "funding_threshold_pipeline"
    assert out["commands"][0]["lane"] == "funding"


def test_research_command_status_rejects_unknown_command_id() -> None:
    from services.analytics.research_command_status import build_research_command_status

    out = build_research_command_status(command_id="missing_command")

    assert out["ok"] is False
    assert out["reason"] == "invalid_command_id"
    assert out["command_id_filter"] == "missing_command"
    assert out["commands"] == []
    assert "funding_threshold_pipeline" in out["available_command_ids"]


def test_research_command_status_rejects_unknown_lane() -> None:
    from services.analytics.research_command_status import build_research_command_status

    out = build_research_command_status(lane="missing_lane")

    assert out["ok"] is False
    assert out["reason"] == "invalid_lane"
    assert out["lane_filter"] == "missing_lane"
    assert out["commands"] == []
    assert "price_action" in out["available_lanes"]


def test_research_command_status_rejects_unknown_input_class() -> None:
    from services.analytics.research_command_status import build_research_command_status

    out = build_research_command_status(input_class="missing_input")

    assert out["ok"] is False
    assert out["reason"] == "invalid_input_class"
    assert out["input_class_filter"] == "missing_input"
    assert out["commands"] == []
    assert "artifact_input" in out["available_input_classes"]


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
    assert all(row["action_required"] is True for row in out["commands"])
    assert all(row["blocking_reason"] in row["reasons"] for row in out["commands"])
    assert all(row["next_action"].startswith("repair research command wiring") for row in out["commands"])


def test_report_research_command_status_cli(monkeypatch, capsys) -> None:
    from scripts.research import report_research_command_status as script

    monkeypatch.setattr(
        script,
        "build_research_command_status",
        lambda repo_root=None, lane=None, input_class=None, command_id=None: {
            "ok": True,
            "lane_filter": lane,
            "input_class_filter": input_class,
            "command_id_filter": command_id,
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

    assert script.main(
        ["--lane", "funding", "--input-class", "state_input", "--command-id", "funding_threshold_pipeline"]
    ) == 0
    out = capsys.readouterr().out
    assert "Research Command Status" in out
    assert "lane_filter=funding" in out
    assert "input_class_filter=state_input" in out
    assert "command_id_filter=funding_threshold_pipeline" in out
    assert "wired=2" in out
    assert "funding_threshold_pipeline" in out


def test_report_research_command_status_cli_prints_available_filters(monkeypatch, capsys) -> None:
    from scripts.research import report_research_command_status as script

    monkeypatch.setattr(
        script,
        "build_research_command_status",
        lambda repo_root=None, lane=None, input_class=None, command_id=None: {
            "ok": False,
            "reason": "invalid_input_class",
            "lane_filter": lane,
            "input_class_filter": input_class,
            "command_id_filter": command_id,
            "available_input_classes": ["archive_input", "artifact_input", "none"],
            "command_count": 0,
            "summary": {
                "wired": 0,
                "not_wired": 0,
                "by_lane": {},
                "by_input_class": {},
            },
            "commands": [],
        },
    )

    assert script.main(["--input-class", "typo"]) == 2
    out = capsys.readouterr().out
    assert "reason=invalid_input_class" in out
    assert "available_input_classes=archive_input,artifact_input,none" in out
