from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/research/databento_data_source_rfc.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_databento_rfc_preserves_no_implementation_authorization() -> None:
    text = _normalized(DOC)

    assert "No implementation, credential setup, package install, data purchase" in text
    assert "campaign, promotion-gate, or execution change is authorized" in text
    assert "No API key is added to the repo or operator docs by this RFC." in text
    assert "No dependency is added." in text
    assert "No data is fetched." in text


def test_databento_rfc_preserves_research_only_scope() -> None:
    text = _normalized(DOC)

    assert "first permitted use is read-only research artifact generation" in text
    assert "must not become a live routing source" in text
    assert "trading venue, promotion-evidence source, or campaign dependency" in text
    assert "No claim is made that Databento data improves profitability." in text


def test_databento_rfc_preserves_required_decisions() -> None:
    text = _normalized(DOC)

    for phrase in (
        "Data products and schemas",
        "Cost and quota control",
        "Credentials and secrets",
        "Symbology",
        "Dataset provenance",
        "Retention",
        "Reliability",
    ):
        assert phrase in text
    assert "monthly cost cap, per-run row cap" in text
    assert "Do not reuse this mapping for order routing." in text


def test_databento_rfc_preserves_hard_boundaries_and_acceptance_criteria() -> None:
    text = _normalized(DOC)

    for phrase in (
        "Research artifacts only.",
        "Read-only client only.",
        "No private order endpoints.",
        "No live, shadow, capped-live, or paper campaign dependency.",
        "No promotion evidence until a separate provenance qualification branch is reviewed.",
        "Tests prove symbol mapping cannot be imported by order-routing modules.",
        "`research_only`, `not_campaign_evidence`, `not_promotion_evidence`, and `not_execution_input`",
    ):
        assert phrase in text


def test_databento_rfc_is_linked_from_pattern_backlog_and_active_backlog() -> None:
    pattern = _text("docs/research/pattern_strategy_backlog.md")
    backlog = _text("REMAINING_TASKS.md")

    assert DOC in pattern
    assert DOC in backlog
