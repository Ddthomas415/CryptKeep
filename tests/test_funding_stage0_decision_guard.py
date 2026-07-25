from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/strategies/funding_extreme_stage0_decision_2026-07-11.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_funding_stage0_decision_preserves_non_promotion_status() -> None:
    text = _normalized(DOC)

    assert "accepted Stage 0 wiring proof; not promoted to persistent campaign" in text
    assert "Keep `funding_extreme_default` as the next high-value profitability research candidate" in text
    assert "do not start a persistent campaign or treat it as promotion evidence yet" in text


def test_funding_stage0_decision_preserves_proof_contract() -> None:
    text = _normalized(DOC)

    assert "using an OKX public-OHLCV proof contract" in text
    assert "`CBP_CRYPTO_EDGE_DB_PATH` / `--strategy-context-db-path` override" in text
    assert "`status=passed`" in text
    assert "`blocking_checks=0`" in text
    assert "`strategy_context_ok=true`, `strategy_context_reason=funding_context_ready`" in text
    assert "`live_public OKX BTC/USDT:USDT`" in text
    assert "`signal_action=hold`, `signal_reason=funding_neutral`" in text
    assert "canonical fill count unchanged: `176`" in text
    assert "challenger fill count: `0`" in text


def test_funding_stage0_decision_preserves_confirmed_and_unconfirmed_boundaries() -> None:
    text = _normalized(DOC)

    for phrase in (
        "the managed paper runner can execute `funding_extreme`",
        "the runner can pair public OHLCV with OKX funding context",
        "the isolated challenger run does not mutate canonical paper fills",
        "positive expectancy",
        "actionable funding-extreme trade behavior",
        "paper-gate qualification for crypto-edge provenance",
        "suitability for persistent paper campaign inclusion",
    ):
        assert phrase in text


def test_funding_stage0_decision_preserves_next_conditions_and_backlog_link() -> None:
    text = _normalized(DOC)
    backlog = _text("REMAINING_TASKS.md")

    assert "Run archive-backed research for `funding_extreme`" in text
    assert "high-risk crypto-edge paper-qualification extension separately" in text
    assert "stale/mismatched edge fixtures must reject" in text
    assert "Decide whether challenger edge-store seeding should remain an operator step" in text
    assert DOC in backlog
    assert (REPO / "services/analytics/funding_stage0_readiness.py").is_file()
    assert (REPO / "services/analytics/funding_stage0_proof_verifier.py").is_file()
