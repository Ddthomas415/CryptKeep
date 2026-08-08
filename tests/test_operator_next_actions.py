from __future__ import annotations


def test_operator_next_actions_combines_research_and_proof_actions(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "research_artifact_actions_required": 1,
                "research_command_actions_required": 1,
                "passive_operator_evidence_actions_required": 2,
                "operator_proof_actions_required": 69,
            },
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run make price-action-research-pipeline",
                    }
                ],
                "research_artifacts": [
                    {
                        "artifact_id": "archive_parameter_sweep",
                        "blocking_reason": "latest_artifact_missing",
                        "next_action": "run make archive-parameter-sweep with accepted research inputs",
                    }
                ],
                "research_commands": [
                    {
                        "command_id": "funding_threshold_pipeline",
                        "blocking_reason": "script_missing",
                        "next_action": "repair research command wiring",
                    }
                ],
                "passive_operator_evidence": [
                    {
                        "ordinal": 1,
                        "text": "Run host proof",
                        "next_action": "collect or record operator evidence",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 12,
                        "category": "remaining_proof",
                        "next_action": "produce or record proof",
                    }
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", max_actions=10)

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["does_not_close_proof"] is True
    assert out["does_not_run_campaigns"] is True
    assert out["does_not_fetch_market_data"] is True
    assert out["does_not_mutate_state"] is True
    assert out["action_count_total"] == 74
    assert out["action_count_available"] == 5
    assert out["action_count_returned"] == 5
    assert out["summary"]["available_by_lane"] == {
        "operator_proof": 1,
        "passive_operator_evidence": 1,
        "research_artifact": 1,
        "research_command": 1,
        "research_pipeline": 1,
    }
    assert out["summary"]["available_by_reason"] == {
        "latest_artifact_missing": 1,
        "latest_summary_missing": 1,
        "passive_operator_evidence": 1,
        "remaining_proof": 1,
        "script_missing": 1,
    }
    assert [row["lane"] for row in out["actions"]] == [
        "research_pipeline",
        "research_artifact",
        "research_command",
        "operator_proof",
        "passive_operator_evidence",
    ]
    assert out["actions"][0]["source"] == "price_action"
    assert out["actions"][1]["source"] == "archive_parameter_sweep"
    assert out["actions"][2]["source"] == "funding_threshold_pipeline"
    assert out["actions"][3]["line"] == 12
    assert out["actions"][4]["source"] == "passive_operator_evidence"
    assert out["actions"][4]["ordinal"] == 1


def test_operator_next_actions_respects_limit(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {"research_pipeline_actions_required": 2, "operator_proof_actions_required": 0},
            "actions": {
                "research_pipelines": [
                    {"pipeline_id": "one", "blocking_reason": "x", "next_action": "a"},
                    {"pipeline_id": "two", "blocking_reason": "y", "next_action": "b"},
                ],
                "operator_proofs": [],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", max_actions=1)

    assert out["action_count_total"] == 2
    assert out["action_count_available"] == 2
    assert out["action_count_returned"] == 1
    assert len(out["actions"]) == 1


def test_operator_next_actions_filters_by_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 2,
                "passive_operator_evidence_actions_required": 3,
                "operator_proof_actions_required": 69,
            },
            "actions": {
                "research_pipelines": [
                    {"pipeline_id": "price_action", "blocking_reason": "missing", "next_action": "run research"}
                ],
                "passive_operator_evidence": [
                    {"ordinal": 1, "text": "Evidence", "next_action": "collect evidence"}
                ],
                "operator_proofs": [
                    {"line": 7, "category": "remaining_proof", "next_action": "produce proof"}
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", lane="operator_proof", max_actions=20)

    assert out["lane_filter"] == "operator_proof"
    assert out["action_count_total"] == 69
    assert out["action_count_available"] == 1
    assert out["action_count_returned"] == 1
    assert [row["lane"] for row in out["actions"]] == ["operator_proof"]


def test_operator_next_actions_fails_closed_on_invalid_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "operator_proof_actions_required": 1,
            },
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "remaining_proof",
                        "next_action": "produce proof",
                    }
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", lane="research")

    assert out["ok"] is False
    assert out["reason"] == "invalid_action_lane"
    assert out["available_action_lanes"] == [
        "roadmap_tracking",
        "backlog_lane",
        "research_pipeline",
        "research_artifact",
        "research_command",
        "operator_read_only_command",
        "passive_operator_evidence",
        "operator_proof",
    ]
    assert out["lane_filter"] == "research"
    assert out["action_count_total"] == 0
    assert out["action_count_available"] == 0
    assert out["actions"] == []


def test_operator_next_actions_surfaces_roadmap_tracking_failure(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": False,
            "reason": "roadmap_tracking_incomplete",
            "report_type": "operator_status_bundle",
            "summary": {
                "roadmap_tracking_actions_required": 1,
                "research_pipeline_actions_required": 0,
                "operator_proof_actions_required": 0,
            },
            "actions": {
                "roadmap_tracking": [
                    {
                        "blocking_reason": "roadmap_tracking_incomplete",
                        "next_action": "repair roadmap tracking links, commands, or boundaries; then run make roadmap-tracking-status-json",
                    }
                ],
                "operator_proofs": [],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", lane="roadmap_tracking")

    assert out["ok"] is False
    assert out["source_reason"] == "roadmap_tracking_incomplete"
    assert out["lane_filter"] == "roadmap_tracking"
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert out["summary"]["available_by_lane"] == {"roadmap_tracking": 1}
    assert out["actions"] == [
        {
            "lane": "roadmap_tracking",
            "source": "roadmap_tracking_status",
            "line": None,
            "blocking_reason": "roadmap_tracking_incomplete",
            "next_action": "repair roadmap tracking links, commands, or boundaries; then run make roadmap-tracking-status-json",
        }
    ]


def test_operator_next_actions_filters_by_passive_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "passive_operator_evidence_actions_required": 3,
                "operator_proof_actions_required": 2,
            },
            "actions": {
                "research_pipelines": [
                    {"pipeline_id": "price_action", "blocking_reason": "missing", "next_action": "run research"}
                ],
                "passive_operator_evidence": [
                    {"ordinal": 1, "text": "Evidence A", "next_action": "collect evidence A"},
                    {"ordinal": 2, "text": "Evidence B", "next_action": "collect evidence B"},
                ],
                "operator_proofs": [
                    {"line": 7, "category": "remaining_proof", "next_action": "produce proof"}
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", lane="passive_operator_evidence", max_actions=20)

    assert out["lane_filter"] == "passive_operator_evidence"
    assert out["action_count_total"] == 3
    assert out["action_count_available"] == 2
    assert out["action_count_returned"] == 2
    assert [row["lane"] for row in out["actions"]] == ["passive_operator_evidence", "passive_operator_evidence"]
    assert [row["ordinal"] for row in out["actions"]] == [1, 2]


def test_operator_next_actions_filters_by_research_command_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "research_artifact_actions_required": 2,
                "research_command_actions_required": 4,
                "operator_proof_actions_required": 2,
            },
            "actions": {
                "research_pipelines": [
                    {"pipeline_id": "price_action", "blocking_reason": "missing", "next_action": "run research"}
                ],
                "research_artifacts": [
                    {
                        "artifact_id": "archive_parameter_sweep",
                        "blocking_reason": "latest_artifact_missing",
                        "next_action": "run archive sweep",
                    }
                ],
                "research_commands": [
                    {
                        "command_id": "funding_threshold_pipeline",
                        "blocking_reason": "script_missing",
                        "next_action": "repair research command wiring",
                    },
                    {
                        "command_id": "price_action_pipeline",
                        "blocking_reason": "make_target_missing",
                        "next_action": "repair price action command wiring",
                    },
                ],
                "operator_proofs": [
                    {"line": 7, "category": "remaining_proof", "next_action": "produce proof"}
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", lane="research_command", max_actions=20)

    assert out["lane_filter"] == "research_command"
    assert out["action_count_total"] == 4
    assert out["action_count_available"] == 2
    assert out["action_count_returned"] == 2
    assert [row["lane"] for row in out["actions"]] == ["research_command", "research_command"]
    assert [row["source"] for row in out["actions"]] == [
        "funding_threshold_pipeline",
        "price_action_pipeline",
    ]


def test_operator_next_actions_backlog_lane_filter_reports_planning_rows_not_actions(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "backlog_lane_actions_required": 2,
                "research_pipeline_actions_required": 1,
                "operator_proof_actions_required": 9,
            },
            "actions": {
                "backlog_lanes": [
                    {
                        "lane_key": "low_risk_docs_tests",
                        "ordinal": 1,
                        "next_action": "select or execute a scoped batch for docs",
                    },
                    {
                        "lane_key": "low_risk_docs_tests",
                        "ordinal": 2,
                        "next_action": "select or execute a scoped batch for tests",
                    },
                ],
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(repo_root=".", backlog_lane="low_risk_docs_tests", max_actions=20)

    assert captured["backlog_lane"] == "low_risk_docs_tests"
    assert out["backlog_lane_filter"] == "low_risk_docs_tests"
    assert out["lane_filter"] is None
    assert out["action_count_total"] == 0
    assert out["action_count_available"] == 0
    assert out["actions"] == []
    assert out["planning_row_count"] == 2
    assert out["planning_rows"] == [
        {
            "lane": "backlog_lane",
            "source": "low_risk_docs_tests",
            "line": None,
            "ordinal": 1,
            "blocking_reason": "backlog_lane_item",
            "next_action": "select or execute a scoped batch for docs",
        },
        {
            "lane": "backlog_lane",
            "source": "low_risk_docs_tests",
            "line": None,
            "ordinal": 2,
            "blocking_reason": "backlog_lane_item",
            "next_action": "select or execute a scoped batch for tests",
        },
    ]


def test_operator_next_actions_forwards_backlog_lane_ordinal(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "backlog_lane_actions_required": 1,
                "source_backlog_lane_actions_required": 3,
                "operator_proof_actions_required": 9,
            },
            "actions": {
                "backlog_lanes": [
                    {
                        "lane_key": "low_risk_docs_tests",
                        "ordinal": 2,
                        "next_action": "select or execute a scoped batch for item two",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(
        repo_root=".",
        backlog_lane="low_risk_docs_tests",
        backlog_lane_ordinal=2,
        max_actions=20,
    )

    assert captured["backlog_lane"] == "low_risk_docs_tests"
    assert captured["backlog_lane_ordinal"] == "2"
    assert out["backlog_lane_filter"] == "low_risk_docs_tests"
    assert out["backlog_lane_ordinal_filter"] == 2
    assert out["action_count_total"] == 0
    assert out["action_count_available"] == 0
    assert out["actions"] == []
    assert out["planning_row_count"] == 1
    assert out["planning_rows"] == [
        {
            "lane": "backlog_lane",
            "source": "low_risk_docs_tests",
            "line": None,
            "ordinal": 2,
            "blocking_reason": "backlog_lane_item",
            "next_action": "select or execute a scoped batch for item two",
        }
    ]


def test_operator_next_actions_filters_by_reason(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {"research_pipeline_actions_required": 1, "operator_proof_actions_required": 2},
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_proofs": [
                    {"line": 7, "category": "remaining_proof", "next_action": "produce proof"},
                    {"line": 8, "category": "host_side_reference", "next_action": "run host proof"},
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", reason="host_side_reference", max_actions=20)

    assert out["reason_filter"] == "host_side_reference"
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert out["summary"]["available_by_reason"] == {"host_side_reference": 1}
    assert [row["blocking_reason"] for row in out["actions"]] == ["host_side_reference"]


def test_operator_next_actions_excludes_reasons_without_hiding_counts(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "operator_proof_actions_required": 3,
                "passive_operator_evidence_actions_required": 2,
            },
            "actions": {
                "operator_proofs": [
                    {"line": 7, "category": "remaining_proof", "next_action": "produce proof"},
                    {"line": 8, "category": "host_side_reference", "next_action": "run host proof"},
                ],
                "passive_operator_evidence": [
                    {"ordinal": 1, "next_action": "collect passive evidence"},
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(
        repo_root=".",
        exclude_reasons=["host_side_reference,passive_operator_evidence"],
        max_actions=20,
    )

    assert out["exclude_reason_filter"] == ["host_side_reference", "passive_operator_evidence"]
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert out["source_summary"]["operator_proof_actions_required"] == 3
    assert out["source_summary"]["passive_operator_evidence_actions_required"] == 2
    assert out["summary"]["available_by_reason"] == {"remaining_proof": 1}
    assert out["actions"] == [
        {
            "lane": "operator_proof",
            "source": "remaining_proof",
            "line": 7,
            "blocking_reason": "remaining_proof",
            "next_action": "produce proof",
        }
    ]


def test_operator_next_actions_filters_by_action_source(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {"research_pipeline_actions_required": 1, "operator_proof_actions_required": 2},
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_proofs": [
                    {"line": 7, "category": "remaining_proof", "next_action": "produce proof"},
                    {"line": 8, "category": "host_side_reference", "next_action": "run host proof"},
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", action_source="host_side_reference", max_actions=20)

    assert out["action_source_filter"] == "host_side_reference"
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert out["summary"]["available_by_lane"] == {"operator_proof": 1}
    assert out["summary"]["available_by_reason"] == {"host_side_reference": 1}
    assert [row["source"] for row in out["actions"]] == ["host_side_reference"]


def test_operator_next_actions_forwards_source_filters(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {"research_pipeline_actions_required": 1, "operator_proof_actions_required": 1},
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(
        repo_root=".",
        backlog_lane="low_risk_docs_tests",
        backlog_lane_ordinal=2,
        research_pipeline="price_action",
        research_artifact_lane="archive",
        research_artifact_id="archive_parameter_sweep",
        research_command_lane="funding",
        research_command_input_class="artifact_input",
        operator_proof_category="host_side_reference",
        operator_proof_line=7,
    )

    assert captured == {
        "backlog_lane": "low_risk_docs_tests",
        "backlog_lane_ordinal": "2",
        "research_pipeline": "price_action",
        "research_artifact_lane": "archive",
        "research_artifact_id": "archive_parameter_sweep",
        "research_command_lane": "funding",
        "research_command_input_class": "artifact_input",
        "research_command_id": None,
        "operator_read_only_medium_lane_item": None,
        "operator_read_only_command_id": None,
        "operator_proof_category": "host_side_reference",
        "operator_proof_line": "7",
        "operator_proof_passive_ordinal": None,
    }
    assert out["backlog_lane_filter"] == "low_risk_docs_tests"
    assert out["backlog_lane_ordinal_filter"] == 2
    assert out["research_pipeline_filter"] == "price_action"
    assert out["research_artifact_lane_filter"] == "archive"
    assert out["research_artifact_id_filter"] == "archive_parameter_sweep"
    assert out["research_command_lane_filter"] == "funding"
    assert out["research_command_input_class_filter"] == "artifact_input"
    assert out["operator_proof_category_filter"] == "host_side_reference"
    assert out["operator_proof_line_filter"] == 7


def test_operator_next_actions_source_filter_implies_matching_action_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {"research_pipeline_actions_required": 1, "operator_proof_actions_required": 9},
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", research_pipeline="price_action", max_actions=20)

    assert out["research_pipeline_filter"] == "price_action"
    assert out["lane_filter"] is None
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert out["actions"] == [
        {
            "lane": "research_pipeline",
            "source": "price_action",
            "line": None,
            "blocking_reason": "latest_summary_missing",
            "next_action": "run research",
        }
    ]


def test_operator_next_actions_single_source_filter_passes_matching_bundle_section(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "source_ok": False,
            "shown_ok": True,
            "report_type": "operator_status_bundle",
            "source_reasons": {"research_artifact_inventory": "hidden_source_unhealthy"},
            "summary": {"operator_read_only_command_actions_required": 0},
            "actions": {"operator_read_only_commands": []},
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(
        repo_root=".",
        operator_read_only_medium_lane_item="platform_event_packet",
        max_actions=20,
    )

    assert captured["section"] == "operator_read_only"
    assert captured["operator_read_only_medium_lane_item"] == "platform_event_packet"
    assert out["ok"] is True
    assert out["source_reasons"] == {"research_artifact_inventory": "hidden_source_unhealthy"}
    assert out["operator_read_only_medium_lane_item_filter"] == "platform_event_packet"
    assert out["action_count_total"] == 0
    assert out["action_count_available"] == 0
    assert out["actions"] == []


def test_operator_next_actions_research_artifact_filter_implies_matching_action_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "research_artifact_actions_required": 2,
                "operator_proof_actions_required": 9,
            },
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "research_artifacts": [
                    {
                        "artifact_id": "archive_parameter_sweep",
                        "blocking_reason": "latest_artifact_missing",
                        "next_action": "run archive sweep",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(repo_root=".", research_artifact_lane="archive", max_actions=20)

    assert captured["research_artifact_lane"] == "archive"
    assert out["research_artifact_lane_filter"] == "archive"
    assert out["lane_filter"] is None
    assert out["action_count_total"] == 2
    assert out["action_count_available"] == 1
    assert out["actions"] == [
        {
            "lane": "research_artifact",
            "source": "archive_parameter_sweep",
            "line": None,
            "blocking_reason": "latest_artifact_missing",
            "next_action": "run archive sweep",
        }
    ]


def test_operator_next_actions_surfaces_invalid_research_pipeline_filter(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": False,
            "report_type": "operator_status_bundle",
            "source_reasons": {"research_pipeline_status": "invalid_pipeline"},
            "summary": {
                "research_pipeline_actions_required": 0,
                "operator_proof_actions_required": 9,
            },
            "actions": {
                "research_pipelines": [],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(repo_root=".", research_pipeline="missing_pipeline", max_actions=20)

    assert captured["research_pipeline"] == "missing_pipeline"
    assert out["ok"] is False
    assert out["research_pipeline_filter"] == "missing_pipeline"
    assert out["source_reasons"] == {"research_pipeline_status": "invalid_pipeline"}
    assert out["action_count_total"] == 0
    assert out["action_count_available"] == 0
    assert out["actions"] == []


def test_operator_next_actions_research_command_filter_implies_matching_action_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "research_command_actions_required": 2,
                "operator_proof_actions_required": 9,
            },
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "research_commands": [
                    {
                        "command_id": "funding_threshold_pipeline",
                        "blocking_reason": "script_missing",
                        "next_action": "repair research command wiring",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(repo_root=".", research_command_lane="funding", max_actions=20)

    assert captured["research_command_lane"] == "funding"
    assert out["research_command_lane_filter"] == "funding"
    assert out["lane_filter"] is None
    assert out["action_count_total"] == 2
    assert out["action_count_available"] == 1
    assert out["actions"] == [
        {
            "lane": "research_command",
            "source": "funding_threshold_pipeline",
            "line": None,
            "blocking_reason": "script_missing",
            "next_action": "repair research command wiring",
        }
    ]


def test_operator_next_actions_research_command_id_filter_implies_matching_action_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "research_command_actions_required": 1,
                "operator_proof_actions_required": 9,
            },
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "research_commands": [
                    {
                        "command_id": "funding_threshold_pipeline",
                        "blocking_reason": "script_missing",
                        "next_action": "repair research command wiring",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(
        repo_root=".",
        research_command_id="funding_threshold_pipeline",
        max_actions=20,
    )

    assert captured["research_command_id"] == "funding_threshold_pipeline"
    assert out["research_command_id_filter"] == "funding_threshold_pipeline"
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert [row["lane"] for row in out["actions"]] == ["research_command"]
    assert [row["source"] for row in out["actions"]] == ["funding_threshold_pipeline"]


def test_operator_next_actions_operator_read_only_filter_implies_matching_action_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    captured = {}

    def fake_bundle(repo_root=None, **filters):
        captured.update(filters)
        return {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "research_pipeline_actions_required": 1,
                "operator_read_only_command_actions_required": 1,
                "operator_proof_actions_required": 9,
            },
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_read_only_commands": [
                    {
                        "command_id": "paper_gate_velocity",
                        "blocking_reason": "script_missing",
                        "next_action": "repair read-only command wiring",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        }

    monkeypatch.setattr(mod, "build_operator_status_bundle", fake_bundle)

    out = mod.build_operator_next_actions(
        repo_root=".",
        operator_read_only_command_id="paper_gate_velocity",
        max_actions=20,
    )

    assert captured["operator_read_only_command_id"] == "paper_gate_velocity"
    assert out["operator_read_only_command_id_filter"] == "paper_gate_velocity"
    assert out["lane_filter"] is None
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert out["actions"] == [
        {
            "lane": "operator_read_only_command",
            "source": "paper_gate_velocity",
            "line": None,
            "blocking_reason": "script_missing",
            "next_action": "repair read-only command wiring",
        }
    ]


def test_operator_next_actions_proof_line_filter_implies_proof_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {"research_pipeline_actions_required": 1, "operator_proof_actions_required": 1},
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run research",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 172,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", operator_proof_line=172, max_actions=20)

    assert out["operator_proof_line_filter"] == 172
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert [row["lane"] for row in out["actions"]] == ["operator_proof"]
    assert [row["line"] for row in out["actions"]] == [172]


def test_operator_next_actions_passive_ordinal_filter_implies_passive_lane(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {
                "passive_operator_evidence_actions_required": 1,
                "operator_proof_actions_required": 1,
            },
            "actions": {
                "passive_operator_evidence": [
                    {"ordinal": 2, "next_action": "collect second passive item"},
                ],
                "operator_proofs": [
                    {
                        "line": 172,
                        "category": "host_side_reference",
                        "next_action": "run host proof",
                    }
                ],
            },
            "operator_proof_passive_ordinal_filter": int(filters.get("operator_proof_passive_ordinal") or 0)
            or None,
        },
    )

    out = mod.build_operator_next_actions(repo_root=".", operator_proof_passive_ordinal=2, max_actions=20)

    assert out["operator_proof_passive_ordinal_filter"] == 2
    assert out["action_count_total"] == 1
    assert out["action_count_available"] == 1
    assert [row["lane"] for row in out["actions"]] == ["passive_operator_evidence"]
    assert [row["ordinal"] for row in out["actions"]] == [2]


def test_report_operator_next_actions_cli(monkeypatch, capsys) -> None:
    from scripts import report_operator_next_actions as script

    monkeypatch.setattr(
        script,
        "build_operator_next_actions",
        lambda repo_root=None, max_actions=20, lane=None, reason=None, action_source=None, **filters: {
            "ok": True,
            "action_count_total": 1,
            "action_count_returned": 1,
            "reason": None,
            "available_action_lanes": [
                "backlog_lane",
                "research_pipeline",
                "research_artifact",
                "research_command",
                "operator_read_only_command",
                "passive_operator_evidence",
                "operator_proof",
            ],
            "lane_filter": lane,
            "reason_filter": reason,
            "exclude_reason_filter": filters.get("exclude_reasons") or [],
            "action_source_filter": action_source,
            "backlog_lane_filter": filters.get("backlog_lane"),
            "backlog_lane_ordinal_filter": int(filters.get("backlog_lane_ordinal") or 0) or None,
            "research_pipeline_filter": filters.get("research_pipeline"),
            "research_artifact_lane_filter": filters.get("research_artifact_lane"),
            "research_artifact_id_filter": filters.get("research_artifact_id"),
            "research_command_lane_filter": filters.get("research_command_lane"),
            "research_command_input_class_filter": filters.get("research_command_input_class"),
            "research_command_id_filter": filters.get("research_command_id"),
            "operator_read_only_medium_lane_item_filter": filters.get("operator_read_only_medium_lane_item"),
            "operator_read_only_command_id_filter": filters.get("operator_read_only_command_id"),
            "operator_proof_category_filter": filters.get("operator_proof_category"),
            "operator_proof_line_filter": int(filters.get("operator_proof_line") or 0) or None,
            "operator_proof_passive_ordinal_filter": int(filters.get("operator_proof_passive_ordinal") or 0)
            or None,
            "summary": {
                "available_by_lane": {"backlog_lane": 1},
                "available_by_reason": {"backlog_lane_item": 1},
            },
            "actions": [
                {
                    "lane": "backlog_lane",
                    "source": "low_risk_docs_tests",
                    "line": None,
                    "ordinal": 1,
                    "blocking_reason": "backlog_lane_item",
                    "next_action": "select or execute a scoped batch",
                }
            ],
        },
    )

    assert script.main(
        [
            "--max-actions",
            "1",
            "--lane",
            "backlog_lane",
            "--reason",
            "backlog_lane_item",
            "--exclude-reason",
            "host_side_reference,passive_operator_evidence",
            "--action-source",
            "low_risk_docs_tests",
            "--backlog-lane",
            "low_risk_docs_tests",
            "--backlog-lane-ordinal",
            "1",
            "--research-pipeline",
            "price_action",
            "--research-artifact-lane",
            "archive",
            "--research-artifact-id",
            "archive_parameter_sweep",
            "--operator-proof-category",
            "host_side_reference",
            "--research-command-id",
            "funding_threshold_pipeline",
            "--operator-read-only-medium-lane-item",
            "gate_diagnostic",
            "--operator-read-only-command-id",
            "paper_gate_velocity",
            "--operator-proof-line",
            "7",
            "--operator-proof-passive-ordinal",
            "1",
        ]
    ) == 0
    out = capsys.readouterr().out
    assert "Operator Next Actions" in out
    assert "actions=1 shown=1" in out
    assert "lane_filter=backlog_lane" in out
    assert "exclude_reason_filter=host_side_reference,passive_operator_evidence" in out
    assert "action_source_filter=low_risk_docs_tests" in out
    assert "backlog_lane_filter=low_risk_docs_tests" in out
    assert "backlog_lane_ordinal_filter=1" in out
    assert "research_pipeline_filter=price_action" in out
    assert "research_artifact_lane_filter=archive" in out
    assert "research_artifact_id_filter=archive_parameter_sweep" in out
    assert "research_command_id_filter=funding_threshold_pipeline" in out
    assert "operator_read_only_medium_lane_item_filter=gate_diagnostic" in out
    assert "operator_read_only_command_id_filter=paper_gate_velocity" in out
    assert "operator_proof_category_filter=host_side_reference" in out
    assert "operator_proof_line_filter=7" in out
    assert "operator_proof_passive_ordinal_filter=1" in out
    assert "by_lane: backlog_lane=1" in out
    assert "by_reason: backlog_lane_item=1" in out
    assert "backlog_lane:low_risk_docs_tests" in out
    assert "select or execute a scoped batch" in out
