from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/CLOCK_VENUE_TIME_SANITY_POLICY.md"

TIMESTAMP_DEPENDENCIES = {
    "Funding age",
    "candle boundaries",
    "order timestamps",
    "reconciliation windows",
    "slippage measurement",
    "daily evidence windows",
}

SHADOW_CHECKS = {
    "host clock is synchronized to UTC/NTP",
    "venue server time is queried when the venue exposes it",
    "observed host-to-venue skew is recorded",
    "quote/fill/signal records carry timezone-aware timestamps",
    "stale-data thresholds are evaluated against monotonic or UTC-safe sources",
    "evidence reports include the clock-check timestamp",
}

CAPPED_LIVE_CHECKS = {
    "host UTC/NTP status",
    "venue time query result or documented venue limitation",
    "max allowed skew threshold and observed value",
    "behavior when skew exceeds threshold",
    "reconciliation window sanity using real or sandbox venue timestamps",
    "operator-visible status command output",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_clock_policy_preserves_timestamp_sensitivity_scope() -> None:
    text = _normalized(DOC)

    assert "timestamp-sensitive shadow or capped-live evidence" in text
    for dependency in TIMESTAMP_DEPENDENCIES:
        assert dependency in text
    assert "misleading evidence if host time or venue time is materially wrong" in text


def test_clock_policy_preserves_required_shadow_cost_evidence_checks() -> None:
    text = _normalized(DOC)

    assert "Before treating shadow slippage/cost evidence as decision-grade:" in text
    for check in SHADOW_CHECKS:
        assert check in text


def test_clock_policy_preserves_required_capped_live_checks() -> None:
    text = _normalized(DOC)

    assert "Before capped-live approval, add a launch-packet proof showing:" in text
    for check in CAPPED_LIVE_CHECKS:
        assert check in text
    assert "timestamp-sensitive live/shadow evidence remains incomplete" in text


def test_launch_checklist_links_clock_policy() -> None:
    launch = _text("docs/LAUNCH_CHECKLIST.md")
    backlog = _text("REMAINING_TASKS.md")

    assert DOC in launch
    assert DOC in backlog
    assert (REPO / DOC).is_file()
