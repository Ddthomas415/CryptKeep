from __future__ import annotations

from pathlib import Path


def _write_minimal_repo(root: Path) -> None:
    from services.analytics.operator_read_only_command_status import OPERATOR_READ_ONLY_COMMANDS

    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "SCRIPTS.md").write_text(
        "\n".join(
            f"{spec.script.removeprefix('scripts/')} make {spec.make_target or '-'}"
            for spec in OPERATOR_READ_ONLY_COMMANDS
        ),
        encoding="utf-8",
    )
    for spec in OPERATOR_READ_ONLY_COMMANDS:
        path = root / spec.script
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    (root / "Makefile").write_text(
        "\n".join(
            f"{spec.make_target}:\n\ttrue"
            for spec in OPERATOR_READ_ONLY_COMMANDS
            if spec.make_target
        ),
        encoding="utf-8",
    )


def test_operator_read_only_command_status_reports_current_repo_wiring() -> None:
    from services.analytics.operator_read_only_command_status import build_operator_read_only_command_status

    out = build_operator_read_only_command_status()

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["planning_only"] is True
    assert out["does_not_run_commands"] is True
    assert out["does_not_run_campaigns"] is True
    assert out["does_not_fetch_market_data"] is True
    assert out["does_not_mutate_state"] is True
    assert out["not_campaign_evidence"] is True
    assert out["not_promotion_evidence"] is True
    assert out["not_execution_input"] is True
    assert out["command_count"] >= 11
    assert out["summary"]["not_wired"] == 0
    assert out["summary"]["by_medium_lane_item"]["gate_diagnostic"] >= 2
    assert out["summary"]["by_medium_lane_item"]["host_status_wrapper"] >= 2
    rows = {row["command_id"]: row for row in out["commands"]}
    assert rows["managed_paper_campaign_planner"]["make_target"] is None
    assert rows["multi_symbol_paper_campaign_planner"]["make_target"] == "plan-multi-symbol-paper-campaigns"
    assert rows["multi_symbol_paper_campaign_planner"]["medium_lane_item"] == "campaign_planner"
    assert rows["multi_symbol_paper_campaign_planner"]["wiring_ok"] is True
    assert rows["managed_paper_campaign_planner"]["script_index_exists"] is True
    assert rows["paper_gate_velocity"]["make_target"] == "status-paper-gate-velocity"
    assert rows["cost_assumptions"]["make_target"] == "check-cost-assumptions"
    assert rows["cost_assumptions"]["medium_lane_item"] == "gate_diagnostic"
    assert rows["edge_cadence"]["make_target"] == "check-edge-cadence"
    assert rows["edge_cadence"]["medium_lane_item"] == "startup_host_diagnostic"
    assert rows["dead_man"]["make_target"] == "check-dead-man"
    assert rows["dead_man"]["medium_lane_item"] == "startup_host_diagnostic"
    assert rows["ai_operator_oversight"]["make_target"] == "ai-operator-oversight"
    assert rows["roadmap_tracking_status"]["make_target"] == "roadmap-tracking-status"
    assert rows["roadmap_tracking_status"]["medium_lane_item"] == "optional_operator_report"
    assert rows["roadmap_tracking_status"]["input_class"] == "repo_artifacts"
    assert rows["supply_chain"]["make_target"] == "check-supply-chain"
    assert rows["supply_chain"]["medium_lane_item"] == "optional_operator_report"
    assert rows["supply_chain"]["input_class"] == "repo_artifacts"
    assert rows["platform_event_packet"]["make_target"] == "platform-event-packet"
    assert rows["platform_event_integrity"]["medium_lane_item"] == "platform_event_packet"


def test_operator_read_only_command_status_filters() -> None:
    from services.analytics.operator_read_only_command_status import build_operator_read_only_command_status

    by_lane = build_operator_read_only_command_status(medium_lane_item="gate_diagnostic")

    assert by_lane["ok"] is True
    assert by_lane["medium_lane_item_filter"] == "gate_diagnostic"
    assert by_lane["summary"]["by_medium_lane_item"] == {"gate_diagnostic": by_lane["command_count"]}
    assert all(row["medium_lane_item"] == "gate_diagnostic" for row in by_lane["commands"])

    by_command = build_operator_read_only_command_status(command_id="system_diagnostics")
    assert by_command["ok"] is True
    assert by_command["command_id_filter"] == "system_diagnostics"
    assert by_command["command_count"] == 1
    assert by_command["commands"][0]["script"] == "scripts/run_system_diagnostics.py"

    by_roadmap = build_operator_read_only_command_status(command_id="roadmap_tracking_status")
    assert by_roadmap["ok"] is True
    assert by_roadmap["command_count"] == 1
    assert by_roadmap["commands"][0]["script"] == "scripts/report_roadmap_tracking_status.py"
    assert by_roadmap["commands"][0]["make_target"] == "roadmap-tracking-status"

    by_cost = build_operator_read_only_command_status(command_id="cost_assumptions")
    assert by_cost["ok"] is True
    assert by_cost["command_count"] == 1
    assert by_cost["commands"][0]["script"] == "scripts/check_cost_assumptions.py"
    assert by_cost["commands"][0]["input_class"] == "local_state"

    by_edge = build_operator_read_only_command_status(command_id="edge_cadence")
    assert by_edge["ok"] is True
    assert by_edge["command_count"] == 1
    assert by_edge["commands"][0]["script"] == "scripts/check_edge_cadence.py"
    assert by_edge["commands"][0]["input_class"] == "local_state"

    by_dead_man = build_operator_read_only_command_status(command_id="dead_man")
    assert by_dead_man["ok"] is True
    assert by_dead_man["command_count"] == 1
    assert by_dead_man["commands"][0]["script"] == "scripts/check_dead_man.py"
    assert by_dead_man["commands"][0]["input_class"] == "local_state"

    by_supply_chain = build_operator_read_only_command_status(command_id="supply_chain")
    assert by_supply_chain["ok"] is True
    assert by_supply_chain["command_count"] == 1
    assert by_supply_chain["commands"][0]["script"] == "scripts/check_supply_chain.py"
    assert by_supply_chain["commands"][0]["input_class"] == "repo_artifacts"


def test_operator_read_only_command_status_filters_platform_event_packet_lane() -> None:
    from services.analytics.operator_read_only_command_status import build_operator_read_only_command_status

    out = build_operator_read_only_command_status(medium_lane_item="platform_event_packet")

    assert out["ok"] is True
    assert out["command_count"] == 4
    assert out["summary"]["by_medium_lane_item"] == {"platform_event_packet": 4}
    assert {row["command_id"] for row in out["commands"]} == {
        "platform_event_journal",
        "platform_event_secrets",
        "platform_event_integrity",
        "platform_event_packet",
    }
    assert all(row["wiring_ok"] is True for row in out["commands"])


def test_operator_read_only_command_status_rejects_unknown_filters() -> None:
    from services.analytics.operator_read_only_command_status import build_operator_read_only_command_status

    bad_lane = build_operator_read_only_command_status(medium_lane_item="missing_lane")
    assert bad_lane["ok"] is False
    assert bad_lane["reason"] == "invalid_medium_lane_item"
    assert bad_lane["commands"] == []

    bad_command = build_operator_read_only_command_status(command_id="missing_command")
    assert bad_command["ok"] is False
    assert bad_command["reason"] == "invalid_command_id"
    assert bad_command["commands"] == []


def test_operator_read_only_command_status_fails_closed_on_wiring_drift(tmp_path: Path) -> None:
    from services.analytics.operator_read_only_command_status import build_operator_read_only_command_status

    _write_minimal_repo(tmp_path)
    (tmp_path / "scripts" / "report_paper_gate_velocity.py").unlink()

    out = build_operator_read_only_command_status(repo_root=tmp_path, command_id="paper_gate_velocity")

    assert out["ok"] is False
    assert out["summary"]["not_wired"] == 1
    assert out["commands"][0]["blocking_reason"] == "script_missing"
    assert out["commands"][0]["next_action"].startswith("repair read-only command wiring")


def test_report_operator_read_only_command_status_cli(monkeypatch, capsys) -> None:
    from scripts import report_operator_read_only_command_status as script

    monkeypatch.setattr(
        script,
        "build_operator_read_only_command_status",
        lambda repo_root=None, medium_lane_item=None, command_id=None: {
            "ok": True,
            "medium_lane_item_filter": medium_lane_item,
            "command_id_filter": command_id,
            "command_count": 1,
            "summary": {
                "wired": 1,
                "not_wired": 0,
                "by_medium_lane_item": {"gate_diagnostic": 1},
                "by_input_class": {"local_state": 1},
            },
            "commands": [
                {
                    "command_id": "paper_gate_velocity",
                    "wiring_ok": True,
                    "medium_lane_item": "gate_diagnostic",
                    "input_class": "local_state",
                    "make_target": "status-paper-gate-velocity",
                    "reasons": [],
                }
            ],
        },
    )

    assert script.main(["--medium-lane-item", "gate_diagnostic", "--command-id", "paper_gate_velocity"]) == 0
    out = capsys.readouterr().out
    assert "Operator Read-Only Command Status" in out
    assert "medium_lane_item_filter=gate_diagnostic" in out
    assert "command_id_filter=paper_gate_velocity" in out
    assert "wired=1" in out
    assert "paper_gate_velocity" in out
