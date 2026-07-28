from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/decisions/paper_promotion_gate_policy_rfc_2026-07-18.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_paper_promotion_rfc_preserves_scope_and_non_goals() -> None:
    text = _normalized(DOC)

    assert "Configurable Paper Promotion Gate Policies" in text
    assert "Preserve strict provenance qualification." in text
    assert "Keep current behavior as the default" in text
    assert "Do not count legacy fills that lack required provenance." in text
    assert "Do not widen the canonical paper universe." in text
    assert "Do not treat five round trips as profitability proof." in text
    assert "Do not mask OHLCV source failures by relaxing promotion gates." in text


def test_paper_promotion_rfc_preserves_policy_classes_and_defaults() -> None:
    text = _normalized(DOC)

    assert "`legacy_round_trip_v1`" in text
    assert "Equivalent to the current machine behavior: 30 days and 10 qualified round trips." in text
    assert "`slow_daily_single_symbol_v1`" in text
    assert "45 calendar days, 60 qualified daily bars, 5 complete qualified round trips" in text
    assert "`intraday_single_symbol_v1`" in text
    assert "`context_edge_v1`" in text
    assert "Must be implemented only after the relevant context qualification branch is reviewed." in text


def test_paper_promotion_rfc_preserves_qualified_bar_definition() -> None:
    text = _normalized(DOC)

    assert "A qualified bar is one unique source-data decision bucket, not one runner loop." in text
    assert "has `ohlcv_sample_mode` explicitly false" in text
    assert "has no `ohlcv_source_mismatch`" in text
    assert "source bar timestamp" in text
    assert "The preferred source bar key is:" in text
    assert "Do not allow this fallback for intraday policies" in text


def test_paper_promotion_rfc_preserves_cohort_and_migration_boundaries() -> None:
    text = _normalized(DOC)

    assert "`promotion.paper.policy.cohort_start` is a read-time filter." in text
    assert "It must not delete, rewrite, or hide older evidence." in text
    assert "Keep current gate output unchanged for all configs without" in text
    assert "Add `slow_daily_single_symbol_v1` to `es_daily_trend_v1` only after this RFC is accepted." in text
    assert "Do not change ES config yet." in text
    assert "Record before/after gate output." in text


def test_paper_promotion_rfc_preserves_ohlcv_reliability_separation_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    assert "OHLCV outages look like slow strategy behavior" in text
    assert "handle OHLCV source failures as a separate blocked-state reliability item" in text
    assert "Do not relax gate thresholds to compensate for source unavailability." in text
    assert "Reviewer agrees OHLCV reliability is handled separately from gate policy." in text
    assert DOC in backlog
