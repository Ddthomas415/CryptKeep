from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/research/crypto_edge_source_decision.md"
PLAN = "sample_data/crypto_edges/live_collector_plan.json"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def _plan() -> dict:
    return json.loads(_text(PLAN))


def test_crypto_edge_source_decision_preserves_read_only_research_scope() -> None:
    text = _normalized(DOC)

    assert "Use OKX as the default read-only derivatives context source" in text
    assert "research data collection for funding, open interest, and basis rows" in text
    assert "It does not approve OKX as a live trading venue" in text
    assert "does not enable derivatives execution" in text
    assert "does not change any order routing, risk gate, promotion gate, or strategy-dispatch behavior" in text


def test_crypto_edge_source_decision_preserves_evidence_basis_and_unknowns() -> None:
    text = _normalized(DOC)

    assert "`research_only=true` and `execution_enabled=false`" in text
    assert "opens public CCXT clients with no API key or secret" in text
    assert "Long-run OKX cadence reliability from the operator host" in text
    assert "positive expectancy after fees, funding, spread, and slippage" in text


def test_crypto_edge_source_decision_preserves_hard_boundaries() -> None:
    text = _normalized(DOC)

    assert "No private credentials are required or authorized by this decision." in text
    assert "No live execution path may consume OKX as a trading venue from this decision." in text
    assert "No strategy may use OKX context rows for promotion evidence" in text
    assert "Any scheduled collector must still prove host cadence" in text


def test_crypto_edge_source_decision_matches_default_collector_plan() -> None:
    plan = _plan()

    for family in ("funding", "open_interest", "basis"):
        assert plan[family], family
        assert {row["venue"] for row in plan[family]} == {"okx"}

    assert {row["venue"] for row in plan["quotes"]} == {"coinbase", "kraken"}
    assert {row["venue"] for row in plan["order_books"]} == {"coinbase"}


def test_crypto_edge_source_decision_preserves_backlog_and_structural_doc_links() -> None:
    backlog = _text("REMAINING_TASKS.md")
    structural = _text("docs/research/crypto_structural_edges.md")

    assert DOC in backlog
    assert PLAN in backlog
    assert DOC in structural
    assert "does not approve OKX as a live" in structural
