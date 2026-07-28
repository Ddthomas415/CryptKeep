from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/decisions/canonical_expectancy_decision.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_canonical_expectancy_decision_preserves_authoritative_source() -> None:
    text = _normalized(DOC)

    assert "RESOLVED - primary paper-history expectancy is authoritative for paper promotion" in text
    assert "provenance-qualified paper-history metrics" in text
    assert "per-closed-trade net expectancy" in text


def test_canonical_expectancy_decision_preserves_jsonl_fallback_boundary() -> None:
    text = _normalized(DOC)

    assert "The JSONL `pnl_usd` fallback is not authoritative for paper promotion" in text
    assert "uses fill-level records and can include opening legs with no realized PnL" in text
    assert "the gate reports expectancy as unknown" in text
    assert "instead of computing a per-fill fallback average" in text


def test_canonical_expectancy_decision_preserves_code_boundary() -> None:
    text = _normalized(DOC)

    assert "`scripts/check_promotion_gates.py::_paper_gate_trade_metrics()`" in text
    assert "`expectancy_ok=None` and `expectancy_value=None`" in text
    assert "for the JSONL fallback path" in text
    assert "The lower-level `_check_expectancy()` helper remains available" in text
    assert "legacy and non-paper contexts" in text
    assert "This decision only changes paper-promotion authority." in text


def test_canonical_expectancy_decision_preserves_authority_rationale_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    assert "A fallback is an authority transition." in text
    assert "Switching from per-closed-trade paper-history expectancy to JSONL per-fill expectancy" in text
    assert "require qualified paper-history metrics" in text
    assert DOC in backlog
