from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

IDENTITY_PHRASES = {
    "profit-measurement and evidence-generation lab",
    "not yet proven to be a profitable trading bot",
    "guarded paper/shadow/live promotion path",
}

UNPROVEN_CAPABILITIES = {
    "archive-backed positive expectancy after costs",
    "real shadow cost/slippage behavior",
    "live execution reliability with capital",
    "profitability across a sustained out-of-sample window",
}

NEAR_TERM_PRIORITIES = {
    "evidence velocity",
    "profitability discovery",
    "cost measurement",
    "safety",
    "recovery",
    "operator wake-up quality",
}

SCOPE_LINKED_DOCS = {
    "README.md",
    "docs/GOLDEN_PATH.md",
    "docs/OBJECTIVE.md",
    "docs/PRODUCT_SURFACE_TRIAGE.md",
}


def _normalized(path: str) -> str:
    return " ".join((REPO / path).read_text(encoding="utf-8").split())


def test_project_identity_scope_doc_preserves_core_boundary() -> None:
    text = _normalized("docs/PROJECT_IDENTITY_AND_SCOPE.md")
    for phrase in IDENTITY_PHRASES:
        assert phrase in text
    for capability in UNPROVEN_CAPABILITIES:
        assert capability in text
    for priority in NEAR_TERM_PRIORITIES:
        assert priority in text


def test_public_entry_docs_link_project_identity_scope() -> None:
    for rel in sorted(SCOPE_LINKED_DOCS):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "PROJECT_IDENTITY_AND_SCOPE.md" in text, rel


def test_project_identity_public_description_does_not_claim_profitability() -> None:
    text = _normalized("docs/PROJECT_IDENTITY_AND_SCOPE.md")
    assert "evidence-first crypto trading research and operations system" in text
    assert "profitable trading bot" in text
    assert "proven profitable trading bot" not in text
