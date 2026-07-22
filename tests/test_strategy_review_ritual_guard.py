from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

RITUAL_INPUTS = {
    "current paper gate output",
    "`make status-paper-all`",
    "paper diagnostics report",
    "loss replay report when losses occurred",
    "strategy hypothesis docs",
    "latest work log/checkpoint changes",
}

RITUAL_OUTPUTS = {
    "campaign health",
    "fills and qualified round trips",
    "wins/losses reviewed",
    "expectancy trend",
    "evidence/provenance failures",
    "strategy hypothesis updates or invalidation notes",
    "decision: continue, investigate, freeze, retire, or rewrite hypothesis",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_strategy_review_ritual_doc_preserves_cadence_inputs_and_outputs() -> None:
    text = _text("docs/STRATEGY_REVIEW_RITUAL.md")

    assert "Run weekly while paper or shadow campaigns are active." in text
    for item in RITUAL_INPUTS:
        assert item in text
    for item in RITUAL_OUTPUTS:
        assert item in text


def test_strategy_review_make_target_preserves_canonical_defaults_and_commands() -> None:
    makefile = _text("Makefile")
    doc = _text("docs/STRATEGY_REVIEW_RITUAL.md")

    assert "STRATEGY_REVIEW_STRATEGY_ID ?= sma_200_trend" in makefile
    assert "STRATEGY_REVIEW_SYMBOL ?= BTC/USDT" in makefile
    assert "STRATEGY_REVIEW_LOSS_LIMIT ?= 10" in makefile
    assert ".PHONY: strategy-review" in makefile
    assert "status-paper-all" in makefile
    assert "scripts/report_paper_run_diagnostics.py" in makefile
    assert "scripts/dev/replay_paper_losses.py" in makefile
    assert "STRATEGY_REVIEW_SYMBOL=BTC/USDT" in doc


def test_strategy_review_ritual_remains_operator_run_and_advisory_only() -> None:
    text = _text("docs/STRATEGY_REVIEW_RITUAL.md")

    assert "Do not run these automatically if the operator has asked to avoid long commands" in text
    assert "The weekly review is advisory." in text
    assert "Any config, strategy, gate, or promotion change" in text
    assert "must be a separate governed change" in text


def test_strategy_review_artifact_is_recorded_and_runbooks_index_links_ritual() -> None:
    runbooks = _text("docs/RUNBOOKS.md")
    checkpoint = REPO / "docs/checkpoints/strategy_review_2026_07_21.md"

    assert "docs/STRATEGY_REVIEW_RITUAL.md" in runbooks
    assert checkpoint.is_file()
    text = checkpoint.read_text(encoding="utf-8")
    assert "Status: advisory review artifact" in text
    assert "make strategy-review" in text
