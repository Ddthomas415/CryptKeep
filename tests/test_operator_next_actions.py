from __future__ import annotations


def test_operator_next_actions_combines_research_and_proof_actions(monkeypatch) -> None:
    import services.analytics.operator_next_actions as mod

    monkeypatch.setattr(
        mod,
        "build_operator_status_bundle",
        lambda repo_root=None, **_filters: {
            "ok": True,
            "report_type": "operator_status_bundle",
            "summary": {"research_pipeline_actions_required": 1, "operator_proof_actions_required": 69},
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run make price-action-research-pipeline",
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
    assert out["action_count_total"] == 70
    assert out["action_count_available"] == 2
    assert out["action_count_returned"] == 2
    assert out["summary"]["available_by_lane"] == {"operator_proof": 1, "research_pipeline": 1}
    assert out["summary"]["available_by_reason"] == {
        "latest_summary_missing": 1,
        "remaining_proof": 1,
    }
    assert [row["lane"] for row in out["actions"]] == ["research_pipeline", "operator_proof"]
    assert out["actions"][0]["source"] == "price_action"
    assert out["actions"][1]["line"] == 12


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
            "summary": {"research_pipeline_actions_required": 2, "operator_proof_actions_required": 69},
            "actions": {
                "research_pipelines": [
                    {"pipeline_id": "price_action", "blocking_reason": "missing", "next_action": "run research"}
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
        research_pipeline="price_action",
        research_command_lane="funding",
        research_command_input_class="artifact_input",
        operator_proof_category="host_side_reference",
        operator_proof_line=7,
    )

    assert captured == {
        "backlog_lane": "low_risk_docs_tests",
        "research_pipeline": "price_action",
        "research_command_lane": "funding",
        "research_command_input_class": "artifact_input",
        "operator_proof_category": "host_side_reference",
        "operator_proof_line": "7",
    }
    assert out["backlog_lane_filter"] == "low_risk_docs_tests"
    assert out["research_pipeline_filter"] == "price_action"
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


def test_report_operator_next_actions_cli(monkeypatch, capsys) -> None:
    from scripts import report_operator_next_actions as script

    monkeypatch.setattr(
        script,
        "build_operator_next_actions",
        lambda repo_root=None, max_actions=20, lane=None, reason=None, action_source=None, **filters: {
            "ok": True,
            "action_count_total": 1,
            "action_count_returned": 1,
            "lane_filter": lane,
            "reason_filter": reason,
            "action_source_filter": action_source,
            "backlog_lane_filter": filters.get("backlog_lane"),
            "research_pipeline_filter": filters.get("research_pipeline"),
            "research_command_lane_filter": filters.get("research_command_lane"),
            "research_command_input_class_filter": filters.get("research_command_input_class"),
            "operator_proof_category_filter": filters.get("operator_proof_category"),
            "operator_proof_line_filter": int(filters.get("operator_proof_line") or 0) or None,
            "summary": {
                "available_by_lane": {"operator_proof": 1},
                "available_by_reason": {"remaining_proof": 1},
            },
            "actions": [
                {
                    "lane": "operator_proof",
                    "source": "remaining_proof",
                    "line": 7,
                    "blocking_reason": "remaining_proof",
                    "next_action": "produce or record proof",
                }
            ],
        },
    )

    assert script.main(
        [
            "--max-actions",
            "1",
            "--lane",
            "operator_proof",
            "--reason",
            "remaining_proof",
            "--action-source",
            "remaining_proof",
            "--research-pipeline",
            "price_action",
            "--operator-proof-category",
            "host_side_reference",
            "--operator-proof-line",
            "7",
        ]
    ) == 0
    out = capsys.readouterr().out
    assert "Operator Next Actions" in out
    assert "actions=1 shown=1" in out
    assert "action_source_filter=remaining_proof" in out
    assert "research_pipeline_filter=price_action" in out
    assert "operator_proof_category_filter=host_side_reference" in out
    assert "operator_proof_line_filter=7" in out
    assert "by_lane: operator_proof=1" in out
    assert "by_reason: remaining_proof=1" in out
    assert "operator_proof:remaining_proof" in out
    assert "produce or record proof" in out
