from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/strategies/paper_universe_widening_decision_2026-07-04.md"

RECONSIDERATION_REQUIREMENTS = {
    "current canonical gate state is recorded from live operator output",
    "symbol-aware chronological",
    "each candidate symbol has venue/source support and provenance qualification",
    "per-symbol risk caps are written",
    "cross-symbol correlation and non-independence are explicitly accepted",
}

PACKET_FIELDS = {
    "candidate symbols and venues",
    "signal source and timeframe per symbol",
    "provenance qualification fixture for each symbol/source",
    "symbol-aware round-trip counting proof",
    "per-symbol and portfolio-level paper risk caps",
    "correlation/non-independence caveat",
    "rollback plan to the current canonical single-symbol campaign",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_paper_universe_decision_preserves_do_not_widen_status() -> None:
    text = _normalized(DOC)

    assert "Status: Do not widen canonical paper universe yet" in text
    assert "Do not widen the canonical `es_daily_trend_v1` paper universe" in text
    assert "active promotion campaign" in text
    assert "canonical promotion evidence is single-symbol-only until a reviewed reconsideration packet" in text
    assert "Multi-symbol paper runs may be used as separate research or challenger evidence" in text
    assert "must not contribute round trips to the canonical `es_daily_trend_v1` promotion gate" in text
    assert "must not use raw or cross-symbol fills to bypass" in text


def test_paper_universe_decision_preserves_reconsideration_requirements() -> None:
    text = _text(DOC)

    for requirement in RECONSIDERATION_REQUIREMENTS:
        assert requirement in text
    for field in PACKET_FIELDS:
        assert field in text


def test_paper_universe_decision_preserves_no_runtime_change_outcome() -> None:
    text = _normalized(DOC)

    assert "No campaign, manifest, strategy config, gate threshold, or runtime process" in text
    assert "changed by this decision" in text


def test_paper_universe_decision_scopes_hetzner_binance_gateio_backlog() -> None:
    text = _normalized(DOC)
    backlog = _normalized("REMAINING_TASKS.md")

    for needle in (
        "Hetzner Binance/Gate.io Paper-Research Backlog Scope",
        "Binance and Gate.io may be evaluated for Hetzner as separate paper/research venue candidates",
        "require OHLCV reachability preflight for each venue/symbol/timeframe",
        "keep Binance behind the existing explicit guard (`CBP_VENUE=binance*` and `CBP_ALLOW_BINANCE=1`)",
        "keep generated evidence isolated from the canonical `es_daily_trend_v1` state directory and gate count",
        "do not add exchange credentials, live routing, order submission, or host package/service mutations",
    ):
        assert needle in text

    assert "Hetzner Binance/Gate.io paper-research venue expansion" in backlog
    assert "no live routing, no order submission, no canonical paper-gate widening" in backlog


def test_backlog_links_paper_universe_decision_record() -> None:
    backlog = _text("REMAINING_TASKS.md")

    assert DOC in backlog
    assert (REPO / DOC).is_file()
