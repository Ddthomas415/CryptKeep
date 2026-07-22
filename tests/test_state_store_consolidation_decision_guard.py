from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/architecture/state_store_consolidation_decision.md"


CURRENT_AUTHORITIES = {
    "`PaperTradingSQLite` / `paper_trading.sqlite`",
    "JSONL evidence plus `TradeJournalSQLite` / `trade_journal.sqlite`",
    "`execution.sqlite` stores such as `ExecutionStore`, intent queues, and",
    "`LivePositionStore` plus risk/fill ledgers in `execution.sqlite`",
    "market/archive/edge stores remain read-only inputs",
}

LONG_TERM_TARGETS = {
    "One transactional execution-accounting boundary per environment",
    "Order lifecycle, fill application, position updates, cash/PnL updates, and",
    "Evidence records remain derivative artifacts",
    "must not become a second accounting authority",
}

IMPLEMENTATION_CONSEQUENCES = {
    "New stores that touch money-adjacent state must be added to",
    "New paper execution features must use `PaperTradingSQLite`",
    "New live/capped-live features must state which execution DB tables they read",
    "Migration work must start with tests and adapters, not broad data movement",
}

CAPPED_LIVE_REQUIREMENTS = {
    "a transactional consolidation migration is implemented and proven",
    "remaining split-store design is explicitly accepted with fault-injection",
    "reconciliation, backup/restore, and operator alerting evidence",
}

FOLLOW_UPS = {
    "Run the targeted caller/migration audit",
    "Add crash-consistency tests",
    "Add backup/restore drill evidence",
    "Revisit this decision after the paper gate clears",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_state_store_decision_preserves_no_migration_boundary() -> None:
    text = _normalized(DOC)

    assert "Status: Accepted direction, implementation deferred" in text
    assert "It does not migrate data, delete stores, or change runtime behavior." in text
    assert "Do not migrate or merge state stores during the active paper evidence campaign." in text
    assert "freeze store ownership, add invariants, and prevent new state surfaces without an owner" in text


def test_state_store_decision_preserves_current_authorities() -> None:
    text = _normalized(DOC)

    for item in CURRENT_AUTHORITIES:
        assert item in text


def test_state_store_decision_preserves_long_term_accounting_target() -> None:
    text = _normalized(DOC)

    for item in LONG_TERM_TARGETS:
        assert item in text


def test_state_store_decision_preserves_implementation_consequences() -> None:
    text = _normalized(DOC)

    for item in IMPLEMENTATION_CONSEQUENCES:
        assert item in text
    assert (REPO / "docs/architecture/storage_surface_classification.md").is_file()


def test_state_store_decision_preserves_capped_live_accepted_risk_boundary() -> None:
    text = _normalized(DOC)

    assert "acceptable for paper and research while promotion remains gated and live execution is blocked" in text
    assert "It is not accepted for capped-live without one of these outcomes:" in text
    for item in CAPPED_LIVE_REQUIREMENTS:
        assert item in text


def test_state_store_decision_preserves_follow_up_requirements_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    for item in FOLLOW_UPS:
        assert item in text
    assert DOC in backlog
