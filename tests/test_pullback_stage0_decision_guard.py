from __future__ import annotations

from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/strategies/pullback_recovery_stage0_decision_2026-07-11.md"
CONFIG = "configs/strategies/pullback_recovery_default.yaml"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def _config() -> dict:
    return yaml.safe_load(_text(CONFIG))


def test_pullback_stage0_decision_preserves_isolated_candidate_status() -> None:
    text = _normalized(DOC)

    assert "Keep `pullback_recovery_default` as an isolated research candidate." in text
    assert "Do not start a persistent paper campaign" in text
    assert "do not mark it as a promotion candidate yet" in text
    assert "does not prove profitability or sufficient trade frequency" in text


def test_pullback_stage0_decision_preserves_stage0_evidence_boundary() -> None:
    text = _normalized(DOC)

    assert "verifier status: `passed`" in text
    assert "blocking checks: `0`" in text
    assert "market data source: `public_ohlcv`" in text
    assert "canonical paper fill count: `176` before and `176` after" in text
    assert "no fills; signal held" in text


def test_pullback_stage0_decision_preserves_required_before_promotion() -> None:
    text = _normalized(DOC)

    for phrase in (
        "archive-backed baseline expectations must be populated",
        "net-fee expectancy must be positive in reproducible research",
        "no-trade filter settings must be accepted or explicitly waived",
        "a separately reviewed campaign manifest must be written",
        "promotion impact on the canonical paper gate must be explicitly scoped",
    ):
        assert phrase in text


def test_pullback_stage0_decision_preserves_allowed_and_not_allowed_uses() -> None:
    text = _normalized(DOC)

    for phrase in (
        "research leaderboard comparison",
        "archive-backed parameter sweeps",
        "isolated one-off proof runs",
        "manual review of generated evidence",
        "persistent daily campaign",
        "promotion candidate status",
        "live, shadow, or capped-live use",
        "changes to canonical paper gate qualification",
    ):
        assert phrase in text


def test_pullback_governance_config_remains_disabled_and_linked() -> None:
    cfg = _config()
    backlog = _text("REMAINING_TASKS.md")

    assert cfg["activation"]["status"] == "governance_only"
    assert cfg["activation"]["campaign_enabled"] is False
    assert cfg["activation"]["promotion_candidate"] is False
    assert cfg["strategy"]["trade_enabled"] is False
    assert DOC in backlog
    assert CONFIG in _text(DOC)
