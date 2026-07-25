from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

LOW_RISK_EXAMPLES = {
    "docs wording",
    "backlog indexing",
    "read-only reports",
    "tests that do not change behavior",
    "operator-command documentation",
}

HIGH_RISK_EXAMPLES = {
    "auth/authz",
    "secrets/config",
    "migrations",
    "deployment scripts",
    "concurrency/cancellation correctness",
    "background jobs",
    "financial logic",
    "promotion gates",
    "live trading execution",
    "order routing",
    "ops risk gates",
    "fail-open behavior",
}

ATTENTION_PRIORITIES = {
    "evidence velocity",
    "profitability discovery",
    "cost measurement",
    "safety",
    "recovery",
    "operator wake-up quality",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_governance_lanes_preserve_low_medium_high_boundaries() -> None:
    text = _text("docs/OPERATOR_GOVERNANCE_LANES.md")

    assert "## Lane 1 - Low Risk" in text
    assert "## Lane 2 - Medium Risk" in text
    assert "## Lane 3 - High Risk" in text

    for example in LOW_RISK_EXAMPLES:
        assert example in text
    for example in HIGH_RISK_EXAMPLES:
        assert example in text

    assert "implementation stops at `READY_FOR_INDEPENDENT_REVIEW`" in text
    assert "This label does not override AGENTS.md" in text


def test_governance_lanes_preserve_operator_attention_cap() -> None:
    text = _text("docs/OPERATOR_GOVERNANCE_LANES.md")

    assert "Every proactive task must tie to at least one of:" in text
    for priority in ATTENTION_PRIORITIES:
        assert priority in text
    assert "If a task does not tie to one of those, defer it." in text


def test_agents_high_risk_rules_remain_stricter_than_lane_labels() -> None:
    agents = _text("AGENTS.md")
    lanes = _normalized("docs/OPERATOR_GOVERNANCE_LANES.md")

    assert "high-risk implementation ends at **READY_FOR_INDEPENDENT_REVIEW**" in agents
    assert "live trading execution, order routing, ops risk gates, and fail-open behavior" in agents
    assert "If AGENTS.md marks the work high-risk, the work is high-risk." in lanes
