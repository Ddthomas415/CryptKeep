from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/AI_COPILOT_OPERATING_RULES.md"

DETERMINISTIC_AUTHORITIES = {
    "order submission",
    "risk enforcement",
    "reconciliation",
    "live arming and halt state",
    "database state transitions",
}

ALLOWED_PROVIDER_FIELDS = {
    "high-level campaign health and status summaries",
    "strategy ids, strategy labels, venue names, and symbols",
    "non-secret gate status, blocker names, and recommendation labels",
    "aggregate fill counts, qualified round-trip counts, and PnL summaries",
    "recent error messages after redaction of secrets",
    "file paths and commit ids that are already part of the repo/audit context",
}

FORBIDDEN_PROVIDER_FIELDS = {
    "API keys, access tokens, signing keys, webhook secrets, or credential prompts",
    "raw exchange authentication headers or account secrets",
    "private SSH material, Tailscale auth links, or cloud-provider write tokens",
    "full unredacted config files",
    "raw SQLite dumps",
    "any field whose only purpose is live order routing, live arming, or",
}

PROVIDER_PROHIBITIONS = {
    "submit orders",
    "change config",
    "promote stages",
    "arm or resume live trading",
    "mark work accepted",
    "override deterministic gates",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_ai_copilot_rules_preserve_deterministic_authority_boundary() -> None:
    text = _text(DOC)

    assert "The deterministic core remains authoritative for:" in text
    assert "The copilot layer is advisory." in text
    for authority in DETERMINISTIC_AUTHORITIES:
        assert authority in text


def test_ai_copilot_rules_preserve_provider_governance_boundary() -> None:
    text = _text(DOC)

    assert "External LLM providers may be used only when an operator explicitly enables" in text
    assert "`CBP_COPILOT_PROVIDER` selects the requested provider." in text
    assert "`CBP_COPILOT_ALLOWED_PROVIDERS=none`" in text
    assert "Unknown or malformed allow-list entries fail closed" in text
    assert "`services/ai_copilot/providers.py` is the only `services/ai_copilot` module" in text
    assert "other copilot modules must go through" in text


def test_ai_copilot_rules_preserve_payload_allow_and_deny_lists() -> None:
    text = _normalized(DOC)

    for field in ALLOWED_PROVIDER_FIELDS:
        assert field in text
    for field in FORBIDDEN_PROVIDER_FIELDS:
        assert field in text


def test_ai_copilot_rules_preserve_advisory_only_provider_summaries() -> None:
    text = _text(DOC)

    assert "Provider-backed summaries are advisory." in text
    for prohibition in PROVIDER_PROHIBITIONS:
        assert prohibition in text
    assert "separate accepted data-disclosure decision" in text


def test_backlog_links_ai_copilot_operating_rules() -> None:
    backlog = _text("REMAINING_TASKS.md")

    assert DOC in backlog
    assert (REPO / DOC).is_file()
