from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/CONFIG_AUTHORITY_DECISION.md"

CANONICAL_RULES = {
    "read final live-enable state through `services.execution.live_arming`",
    "write final live-enable state through `set_live_enabled()`",
    "do not introduce new aliases for `execution.live_enabled`",
    "treat `live.enabled`, `live_trading.enabled`, and risk-local enable flags as",
    "fail closed when trading-critical config is unreadable or malformed",
}

STRATEGY_CONFIG_RULES = {
    "strategy contracts belong in `configs/strategies/`",
    "campaign manifests belong in `configs/paper_evidence_campaigns*.json`",
    "stage transitions require explicit decision records and",
    "not silent config edits",
}

COMPATIBILITY_RULES = {
    "read-only or write-through to the canonical field",
    "covered by tests that show canonical precedence",
    "visible in the work log when touched",
    "retired or explicitly accepted before capped live",
}

CAPPED_LIVE_PROOFS = {
    "a config-reader inventory for live, risk, dashboard, preflight, and executor",
    "proof that `execution.live_enabled` is the only final live-enable authority",
    "corrupt-config fail-closed tests for trading-critical readers",
    "one startup from the documented config bundle",
    "remaining compatibility shims with accepted rationale and",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_config_authority_decision_preserves_canonical_live_rules() -> None:
    text = _normalized(DOC)

    assert "Status: `POLICY_DOCUMENTED`" in text
    for rule in CANONICAL_RULES:
        assert rule in text


def test_config_authority_decision_preserves_strategy_and_campaign_config_rules() -> None:
    text = _normalized(DOC)

    for rule in STRATEGY_CONFIG_RULES:
        assert rule in text


def test_config_authority_decision_preserves_compatibility_policy() -> None:
    text = _normalized(DOC)

    for rule in COMPATIBILITY_RULES:
        assert rule in text


def test_config_authority_decision_preserves_capped_live_proof_requirements() -> None:
    text = _normalized(DOC)

    assert "Before capped-live approval, record:" in text
    for proof in CAPPED_LIVE_PROOFS:
        assert proof in text


def test_launch_checklist_links_config_authority_decision() -> None:
    launch = _text("docs/LAUNCH_CHECKLIST.md")
    backlog = _text("REMAINING_TASKS.md")

    assert DOC in launch
    assert DOC in backlog
    assert (REPO / DOC).is_file()
