from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/research/strategy_expansion_roadmap.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_strategy_expansion_roadmap_preserves_conservative_principles() -> None:
    text = _normalized(DOC)

    for phrase in (
        "prove edge credibility before adding optimization",
        "extend existing repo lanes before opening new architecture branches",
        "keep all new research work behind the current execution and promotion boundaries",
        "validating and weighting edges better, not from adding many more unproven strategy families",
    ):
        assert phrase in text


def test_strategy_expansion_roadmap_reflects_existing_walk_forward_tooling() -> None:
    text = _normalized(DOC)

    assert "Status: research tooling exists; use it before strategy expansion decisions." in text
    assert "`<your-repo-path>/scripts/research/run_archive_walk_forward.py`" in text
    assert "`<your-repo-path>/scripts/research/run_archive_parameter_sweep.py`" in text
    assert "complete archived OHLCV windows, dataset hashes, config hashes, and explicit fee/slippage assumptions" in text
    assert "treat outputs as review inputs for strategy research, not automatic runtime decisions" in text
    assert "no auto-promotion from walk-forward results alone" in text


def test_strategy_expansion_roadmap_reflects_existing_strategy_feedback_ledger() -> None:
    text = _normalized(DOC)

    assert "Status: research ledger exists; use it as conservative research weighting only." in text
    assert "`<your-repo-path>/services/analytics/strategy_feedback.py`" in text
    assert "`<your-repo-path>/docs/research/strategy_feedback_ledger.md`" in text
    assert "compute closed-trade feedback, net realized PnL, expectancy per closed trade, win rate, drawdown, sample size, venue coverage, and recent performance" in text
    assert "research leaderboard weighting" in text
    assert "strategy lab recommendations" in text


def test_strategy_expansion_roadmap_preserves_non_authority_and_ordering_boundaries() -> None:
    text = _normalized(DOC)

    for phrase in (
        "no promotion, strategy-config, position-sizing, campaign, live-routing, or execution authority from feedback weighting",
        "no direct execution from funding/basis alone",
        "no hyperopt-driven promotion without separate evidence review",
        "no “alert fires, order executes directly” bypass",
        "no premature live microstructure execution logic",
        "no Databento-backed execution path before a separate read-only data-source RFC",
        "do not add hyperopt before walk-forward validation",
        "do not add many new strategies before the current strategy-feedback loop exists",
        "do not treat this roadmap as an implementation approval",
    ):
        assert phrase in text
