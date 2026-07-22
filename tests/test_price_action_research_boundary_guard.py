from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/research/pattern_strategy_backlog.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_price_action_backlog_preserves_research_only_status() -> None:
    text = _normalized(DOC)

    assert "Status: research-only label tooling added; strategy use remains deferred." in text
    assert "Treat the labels as context/confirmation features first, not strategy authorities." in text
    assert "Avoid adding another persistent campaign" in text
    assert "joined to existing forward-return and walk-forward artifacts" in text


def test_price_action_backlog_preserves_core_label_scope() -> None:
    text = _normalized(DOC)

    for label in (
        "`engulfing_candle`",
        "`rejection_wick`",
        "`swing_failure`",
        "`break_and_retest`",
        "`fair_value_gap`",
        "`displacement_bar`",
        "`opening_range_state`",
        "`manipulation_candidate`",
    ):
        assert label in text


def test_price_action_backlog_preserves_artifact_and_non_authority_flags() -> None:
    text = _normalized(DOC)

    for flag in (
        "`research_only`",
        "`not_strategy_config`",
        "`not_campaign_evidence`",
        "`not_promotion_evidence`",
        "`not_profitability_evidence`",
    ):
        assert flag in text
    assert "per-bar labels with no trade decisions" in text
    assert "descriptive stability evidence only, not a strategy-selection or confirmation-filter authority" in text


def test_price_action_backlog_preserves_data_source_deferrals() -> None:
    text = _normalized(DOC)

    assert "Use the existing OHLCV archive first for candle/session labels." in text
    assert "Defer volume profile until trade/tick or stronger intraday volume data exists." in text
    assert "Defer Databento to a separate read-only data-source RFC." in text
    assert "API-key, cost, dataset/schema, symbology" in text


def test_price_action_backlog_preserves_acceptance_before_strategy_use_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    for phrase in (
        "Join labels to forward returns after fees/slippage.",
        "Compare label-conditioned returns against unconditioned baseline.",
        "Show out-of-sample stability across multiple windows.",
        "Review separately before using any label as a confirmation filter",
        "Do not promote a new pattern strategy from idea to campaign without:",
        "Do not promote a price-action label directly to execution authority.",
    ):
        assert phrase in text
    assert DOC in backlog
