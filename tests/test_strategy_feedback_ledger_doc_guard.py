from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/research/strategy_feedback_ledger.md"
ROADMAP = "docs/research/strategy_expansion_roadmap.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_strategy_feedback_ledger_preserves_source_and_scope() -> None:
    text = _normalized(DOC)

    assert "research-only strategy feedback ledger derived from persisted paper fills" in text
    assert "loads persisted paper fills from `journal_fills`" in text
    assert "normalizes fills to known strategy IDs" in text
    assert "computes realized closed-trade feedback by strategy" in text
    assert "derives conservative research-only leaderboard adjustments" in text


def test_strategy_feedback_ledger_preserves_non_authority_boundary() -> None:
    text = _normalized(DOC)

    for phrase in (
        "feedback weighting may adjust research leaderboard scores only",
        "feedback weighting is not promotion authority",
        "feedback weighting is not strategy configuration authority",
        "feedback weighting is not position-sizing authority",
        "feedback weighting is not campaign, live-routing, or execution authority",
        "any use beyond research ranking requires a separate reviewed config, campaign, gate, or execution change with its own proof",
    ):
        assert phrase in text


def test_strategy_feedback_ledger_preserves_profitability_caveat_and_roadmap_link() -> None:
    text = _normalized(DOC)
    roadmap = _text(ROADMAP)

    assert "no claim that persisted paper feedback alone proves a profitable edge" in text
    assert "does persisted paper-trade behavior provide enough strategy-specific evidence to slightly reweight research ranking without changing live risk controls?" in text
    assert "strategy feedback ledger" in roadmap
    assert "do not add many new strategies before the current strategy-feedback loop exists" in roadmap
