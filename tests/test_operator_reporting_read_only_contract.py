from __future__ import annotations

from services.analytics.backlog_lane_status import build_backlog_lane_status
from services.analytics.operator_next_actions import build_operator_next_actions
from services.analytics.operator_proof_status import build_operator_proof_status
from services.analytics.operator_status_bundle import build_operator_status_bundle
from services.analytics.research_command_status import build_research_command_status
from services.analytics.research_pipeline_status import build_research_pipeline_status


def test_operator_planning_reports_remain_read_only_and_non_mutating() -> None:
    reports = [
        build_backlog_lane_status(lane="low_risk_docs_tests"),
        build_operator_proof_status(category="host_side_reference"),
        build_operator_status_bundle(section="backlog", backlog_lane="low_risk_docs_tests"),
        build_operator_next_actions(backlog_lane="low_risk_docs_tests", backlog_lane_ordinal=1),
    ]

    for payload in reports:
        assert payload["read_only"] is True
        assert payload["planning_only"] is True

    for payload in reports[1:]:
        assert payload["does_not_run_campaigns"] is True
        assert payload["does_not_fetch_market_data"] is True
        assert payload["does_not_mutate_state"] is True
        assert payload["does_not_close_proof"] is True


def test_operator_research_status_reports_are_not_evidence_or_execution_inputs() -> None:
    reports = [
        build_research_pipeline_status(pipeline="price_action"),
        build_research_command_status(command_id="research_command_status"),
    ]

    for payload in reports:
        assert payload["read_only"] is True
        assert payload["not_campaign_evidence"] is True
        assert payload["not_execution_input"] is True
        assert payload["not_promotion_evidence"] is True

    assert reports[0]["not_strategy_config"] is True
    assert reports[1]["not_research_execution"] is True
