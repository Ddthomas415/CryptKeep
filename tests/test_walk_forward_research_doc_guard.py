from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/research/walk_forward_validation.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_walk_forward_doc_preserves_archive_backed_scope_and_tooling_links() -> None:
    text = _normalized(DOC)

    assert "research-only archive-backed walk-forward and bounded parameter-sweep tooling" in text
    for path in (
        "`services/backtest/walk_forward.py`",
        "`services/backtest/parameter_sweep.py`",
        "`scripts/research/run_archive_walk_forward.py`",
        "`scripts/research/run_archive_parameter_sweep.py`",
    ):
        assert path in text


def test_walk_forward_doc_preserves_fail_closed_archive_and_hash_requirements() -> None:
    text = _normalized(DOC)

    assert "complete-archive reads only" in text
    assert "incomplete archives fail closed instead of falling back to live fetches" in text
    assert "dataset hash, strategy config hash, and source archive metadata" in text
    assert "accepted archive source and dataset hashes" in text


def test_walk_forward_doc_preserves_bounded_sweep_non_authority_boundary() -> None:
    text = _normalized(DOC)

    assert "explicit, bounded parameter-grid expansion" in text
    assert "no unbounded or background parameter search" in text
    assert "no automatic top-variant adoption" in text
    assert "no use as a promotion gate or live-routing control" in text
    assert "no claim that walk-forward or sweep output proves profitability" in text
    assert "The output is input to review. It is not itself strategy authority." in text


def test_walk_forward_doc_preserves_review_before_runtime_use_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    for phrase in (
        "explicit fee/slippage assumptions for the run",
        "minimum sample-size and closed-trade review",
        "comparison against baseline/unconditioned behavior",
        "review of overfitting risk before top variants influence configs",
        "separate reviewed config or campaign change before any runtime use",
    ):
        assert phrase in text
    assert DOC in backlog
