from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _normalized(rel: str) -> str:
    return " ".join((REPO / rel).read_text(encoding="utf-8").split())


def test_directional_plan_locks_project_direction() -> None:
    text = _normalized("docs/PROJECT_DIRECTIONAL_PLAN.md")

    required = {
        "event-driven trading intelligence platform built as a modular monolith",
        "not a single BTC paper-gate project",
        "The paper gate is one validation track inside the broader platform",
        "The LLM/research layer investigates and explains",
        "deterministic risk and execution engine is the only authority allowed to move capital",
    }

    for phrase in required:
        assert phrase in text


def test_directional_plan_keeps_architecture_tied_to_outcomes() -> None:
    text = _normalized("docs/PROJECT_DIRECTIONAL_PLAN.md")

    for outcome in (
        "research velocity",
        "evidence quality",
        "operational safety",
        "maintainability",
    ):
        assert outcome in text

    assert "should not be prioritized" in text


def test_directional_plan_pins_minimal_event_journal_scope() -> None:
    text = _normalized("docs/PROJECT_DIRECTIONAL_PLAN.md")

    for event_type in (
        "CampaignStarted",
        "CampaignEnded",
        "StrategySignalProduced",
        "RiskDecisionMade",
        "EvidenceArtifactGenerated",
    ):
        assert event_type in text

    assert "one concrete producer and one concrete consumer" in text


def test_directional_plan_blocks_architecture_review_loops() -> None:
    text = _normalized("docs/PROJECT_DIRECTIONAL_PLAN.md")

    triggers = {
        "implementation exposes a concrete limitation",
        "research results change system requirements",
        "operational failures repeat",
        "project scope materially changes",
    }

    assert "Do not commission another broad architecture review" in text
    for trigger in triggers:
        assert trigger in text


def test_readme_links_directional_plan() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    normalized = " ".join(readme.split())
    assert "docs/PROJECT_DIRECTIONAL_PLAN.md" in readme
    assert "event-driven trading intelligence platform" in readme
    assert "docs/CURRENT_SYSTEM_DIAGRAM.md" in readme
    assert "docs/REPO_LAYOUT.md" in readme
    assert "docs/strategies/symbol_selection_current_boundary.md" in readme
    assert "docs/research/stock_options_requirements.md" in readme
    assert "neither document authorizes campaign, promotion-gate, broker, or live-execution changes" in readme
    assert "make operator-status-json" in readme
    assert "combined roadmap, backlog, research, read-only command, and proof status bundle" in normalized
