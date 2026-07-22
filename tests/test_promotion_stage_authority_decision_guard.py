from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/decisions/promotion_stage_authority_decision.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_promotion_stage_decision_preserves_gate_enforced_entrypoint() -> None:
    text = _normalized(DOC)

    assert "RESOLVED - gate-enforced operator entrypoint" in text
    assert "documented operator promotion path must consume the promotion-gate verdict" in text
    assert "before it mutates deployment stage" in text
    assert "A promotion command that cannot verify a ready gate fails closed." in text


def test_promotion_stage_decision_preserves_implemented_boundary() -> None:
    text = _normalized(DOC)

    assert "`scripts/show_control_kernel_status.py --promote`" in text
    assert "`scripts/check_promotion_gates.py::run_check()`" in text
    assert "before calling `deployment_stage.promote()`" in text


def test_promotion_stage_decision_preserves_strategy_scope_boundary() -> None:
    text = _normalized(DOC)

    assert "Current machine gate support is scoped to `es_daily_trend_v1`." in text
    assert "Promotion of any other strategy through this entrypoint is blocked" in text
    assert "explicit gate implementation or authorization model" in text


def test_promotion_stage_decision_preserves_authority_rationale_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    assert "`deployment_stage.promote()` changes allocation authority." in text
    assert "Makefile/README path previously reached that mutation without consuming the gate verdict" in text
    assert "preserving the low-level stage-machine API" in text
    assert DOC in backlog
