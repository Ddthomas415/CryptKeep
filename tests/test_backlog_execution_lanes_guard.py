from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/BACKLOG_EXECUTION_LANES.md"
BACKLOG = "REMAINING_TASKS.md"

LANES = {
    "Passive/operator evidence",
    "Low-risk docs/tests",
    "Medium-risk runtime/read-only",
    "High-risk gate/execution/deploy",
}

HIGH_RISK_SURFACES = {
    "Decimal/quantization migration",
    "config authority consolidation",
    "daily-loss gross-vs-net policy",
    "Position-truth reconciliation authority",
    "promotion-gate qualification extension",
    "archive/sweep results to influence campaigns",
    "live/shadow execution, order routing, risk-gate, config/secrets",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_backlog_execution_lanes_preserves_source_of_truth_and_scope() -> None:
    text = _normalized(DOC)

    assert "`REMAINING_TASKS.md` is the source of truth for backlog content." in text
    assert "planning/control artifact only" in text
    assert "It does not close runtime proof." in text
    assert DOC in _text(BACKLOG)


def test_backlog_execution_lanes_preserves_lane_definitions() -> None:
    text = _text(DOC)

    for lane in LANES:
        assert lane in text
    assert "Requires fresh host output, elapsed campaign time, credentials, venue access, or a human decision." in text
    assert "Documentation, classification, read-only reports, or tests that do not alter runtime behavior." in text
    assert "Read-only scripts, reports, planners, or diagnostics that touch runtime state but do not mutate trading behavior." in text
    assert "Promotion gates, financial logic, live/shadow execution, risk gates, config/secrets" in text


def test_backlog_execution_lanes_preserves_completed_item_warning() -> None:
    text = _normalized(DOC)

    assert "Do not rebuild those items unless the current source code lacks them." in text
    assert "operational proof, review/merge follow-through, or deferred capped-live work" in text


def test_backlog_execution_lanes_preserves_high_risk_boundaries() -> None:
    text = _text(DOC)
    normalized = _normalized(DOC)

    assert "These must not be grouped with low-risk cleanup." in text
    assert "They require independent review under `AGENTS.md`" in normalized
    for surface in HIGH_RISK_SURFACES:
        assert surface in text


def test_backlog_execution_lanes_preserves_batching_rule_and_next_order() -> None:
    text = _normalized(DOC)

    assert "Batch only items from the same lane." in text
    assert "If a patch starts in the low-risk lane and discovers it needs to modify a high-risk surface, split the work:" in text
    assert "Stop that implementation at `READY_FOR_INDEPENDENT_REVIEW`." in text
    assert "The current bottleneck is mostly operator evidence" in text
    assert "Low-risk docs/tests only" in text
    assert "Medium-risk read-only research/reporting only" in text
    assert "One high-risk objective at a time" in text


def test_backlog_execution_lanes_preserves_executable_guard_non_authority() -> None:
    text = _normalized(DOC)

    assert "`tests/test_backlog_execution_lanes_guard.py` pins the lane definitions" in text
    assert "The guard is documentation only; it does not decide any backlog item or authorize implementation." in text
