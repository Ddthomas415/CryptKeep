from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/decisions/strategy_selection_authority_decision.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_strategy_selection_decision_preserves_execution_authority() -> None:
    text = _normalized(DOC)

    assert "RESOLVED - Option A adopted" in text
    assert "The configured strategy identity is the only execution authority" in text
    assert "`strategy_selector` and advisor output are advisory only" in text
    assert "must not become the executed strategy through a fallback chain" in text


def test_strategy_selection_decision_preserves_resolution_boundary() -> None:
    text = _normalized(DOC)

    assert "The enforcement boundary is the `strategy_runner` resolution point" in text
    assert 'selected_strategy = str(cfg.get("strategy_id") or "")' in text
    assert "A missing strategy name still resolves to the accepted `ema_cross` default" in text
    assert "explicitly empty or unsupported identity remains empty/unsupported" in text
    assert "`ok=false`, `unknown_strategy`," in text
    assert "`hold`" in text


def test_strategy_selection_decision_preserves_synthetic_evidence_boundary() -> None:
    text = _normalized(DOC)

    assert "The synthetic-tick path did not use `selected_strategy` as execution authority" in text
    assert "executes from the validated strategy block" in text
    assert "evidence-integrity risk by labelling an invalid identity as `ema_cross`" in text
    assert "same no-substitution rule applies there as well" in text


def test_strategy_selection_decision_preserves_invariants_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    assert "Advisory selector output may be recorded as context but may not execute." in text
    assert "Explicitly invalid strategy identity fails closed; it is not substituted." in text
    assert "Missing strategy name continues to use the existing `ema_cross` default." in text
    assert "Synthetic execution continues to use the strategy block" in text
    assert DOC in backlog
