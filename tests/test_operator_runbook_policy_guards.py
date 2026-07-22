from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

STRATEGY_DECISIONS = {
    "keep_paper",
    "freeze",
    "retire",
    "advance_to_shadow_review",
    "rewrite_hypothesis",
}

RETIREMENT_TRIGGERS = {
    "Negative qualified expectancy",
    "Weak sample plus negative direction",
    "Backtest divergence",
    "Repeated evidence failure",
    "Drawdown breach",
    "Operational defect",
    "Thesis violation",
    "Cost-stack failure",
}

FIRST_HOUR_PRECONDITIONS = {
    "paper machine gate is clear from fresh operator-host output",
    "manual strategy review is written and accepted",
    "shadow would-be-fill recorder is implemented and accepted",
    "live routing remains disabled",
    "kill switch status is known and reachable",
}

FIRST_HOUR_ABORTS = {
    "live routing is enabled unexpectedly",
    "any venue order is created",
    "shadow evidence is missing `_stage=shadow`",
    "would-be-fill evidence is not written",
    "operator cannot verify kill-switch status",
}

CONTINUITY_FORBIDDEN_ACTIONS = {
    "enable live trading",
    "promote stage",
    "change strategy configs",
    "rotate secrets without a written incident reason",
    "merge high-risk PRs",
}

CONTINUITY_OPEN_PROOFS = {
    "a backup restore rehearsal",
    "a stopped-campaign recovery rehearsal",
    "a dead-man alert delivery test",
    "evidence that a non-live emergency stop is usable without chat history",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_strategy_stop_policy_preserves_decisions_and_retirement_triggers() -> None:
    text = _text("docs/STRATEGY_STOP_AND_RETIREMENT_POLICY.md")

    assert "Does not authorize live trading." in text
    assert "If a source is missing, classify the decision as `INCOMPLETE`" in text
    for decision in STRATEGY_DECISIONS:
        assert f"`{decision}`" in text
    for trigger in RETIREMENT_TRIGGERS:
        assert trigger in text
    assert "Do not promote a strategy on raw all-history fills" in text
    assert "Do not treat 10 round trips as profitability proof." in text


def test_strategy_stop_policy_preserves_project_thesis_gate() -> None:
    text = _normalized("docs/STRATEGY_STOP_AND_RETIREMENT_POLICY.md")

    assert "Project-Level Thesis Gate" in text
    assert "positive walk-forward expectancy after measured or conservatively modeled" in text
    assert "revise the thesis, change strategy family/horizon, or" in text
    assert "profitability measurement, not a profitable trading system" in text


def test_paper_to_shadow_first_hour_runbook_preserves_safety_boundary() -> None:
    text = _normalized("docs/PAPER_TO_SHADOW_FIRST_HOUR_RUNBOOK.md")

    assert "operator checklist, not an automatic promotion script" in text
    for precondition in FIRST_HOUR_PRECONDITIONS:
        assert precondition in text
    assert "Verify live intent/order tables remain unchanged." in text
    assert "Verify no venue orders exist from the shadow session." in text
    for abort in FIRST_HOUR_ABORTS:
        assert abort in text
    assert "This document does not prove the first hour has been rehearsed." in text


def test_single_operator_continuity_preserves_fail_safe_absence_rules() -> None:
    text = _normalized("docs/SINGLE_OPERATOR_CONTINUITY.md")

    assert "Status: written, not drilled" in text
    assert "the system must fail toward no new risk" in text
    assert "no live promotion or stage change occurs" in text
    assert "no strategy advances stage automatically" in text
    assert "Freeze promotion decisions until a fresh gate/status checkpoint is written." in text
    for action in CONTINUITY_FORBIDDEN_ACTIONS:
        assert action in text
    for proof in CONTINUITY_OPEN_PROOFS:
        assert proof in text


def test_runbooks_index_links_operator_policy_docs() -> None:
    text = _text("docs/RUNBOOKS.md")
    for rel in (
        "docs/PAPER_TO_SHADOW_FIRST_HOUR_RUNBOOK.md",
        "docs/SINGLE_OPERATOR_CONTINUITY.md",
        "docs/STRATEGY_STOP_AND_RETIREMENT_POLICY.md",
    ):
        assert rel in text
        assert (REPO / rel).is_file(), rel
