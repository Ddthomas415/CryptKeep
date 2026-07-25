from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "LAUNCH_CHECKLIST.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8", errors="replace")


def test_launch_checklist_is_a_pass_fail_live_gate():
    text = _text()

    assert "This checklist must be completed and passing before live mode may be armed" in text
    assert "It is a pass/fail gate, not a judgment call." in text
    assert "Complete each section in order. Do not skip sections." in text
    assert "**Do not arm live trading until this checklist is signed off.**" in text


def test_launch_checklist_guard_is_documented():
    text = _text()

    assert "Executable guard:" in text
    assert "tests/test_launch_checklist_guard.py" in text
    assert "required proof packets, drills, paper-gate evidence" in text
    assert "first-live notional caps" in text


def test_launch_checklist_keeps_required_sections():
    text = _text()

    for heading in (
        "## Section 1 — Environment",
        "## Section 2 — Configuration",
        "## Section 3 — Drills",
        "## Section 4 — Paper trading gate",
        "## Section 5 — First live notional cap",
        "## Section 6 — Sign-off",
    ):
        assert heading in text


def test_launch_checklist_preserves_configuration_proof_packets():
    text = _text()

    required = {
        "2.10": "docs/SERVER_SECRETS_ROTATION_MODEL.md",
        "2.11": "docs/SUPPLY_CHAIN_RELEASE_POLICY.md",
        "2.12": "docs/CONFIG_AUTHORITY_DECISION.md",
        "2.13": "docs/CLOCK_VENUE_TIME_SANITY_POLICY.md",
        "2.14": "docs/OPERATOR_ACTION_AUDIT_COVERAGE.md",
    }
    for item, doc in required.items():
        assert f"| {item} |" in text
        assert f"`{doc}`" in text
        assert "proof complete" in text or "policy satisfied or waived" in text


def test_launch_checklist_preserves_drill_set_and_pass_criteria():
    text = _text()

    drills = (
        "### Drill 3.1 — Kill switch drill",
        "### Drill 3.2 — Restart drill",
        "### Drill 3.3 — Stale data drill",
        "### Drill 3.4 — Reconciliation drift drill",
        "### Drill 3.5 — WebSocket reconnect drill",
        "### Drill 3.6 — Rollback drill",
        "### Drill 3.7 — Full-state backup/restore drill",
    )
    for drill in drills:
        assert drill in text

    for criterion in (
        "No orders submitted after halt.",
        "Intent state is consistent after restart.",
        "Submissions blocked during stale period.",
        "Stale intent detected and marked error",
        "No orders during gap.",
        "Preflight correctly blocks bad config.",
        "Restored state matches manifest",
    ):
        assert criterion in text


def test_launch_checklist_preserves_paper_gate_and_cost_evidence_checks():
    text = _text()

    assert "| 4.1 | Minimum paper trading duration |" in text
    assert "| 4.2 | Paper fill rate matches expected strategy frequency |" in text
    assert "| 4.7 | Evidence-write failure status is visible |" in text
    assert "`docs/EVIDENCE_WRITE_FAILURE_STATUS_POLICY.md` proof complete" in text
    assert "| 4.8 | Execution-cost research packet is accepted or explicitly deferred |" in text
    assert "`docs/EXECUTION_COST_RESEARCH_POLICY.md` recommendation recorded" in text


def test_launch_checklist_preserves_first_live_caps_and_signoff_fields():
    text = _text()

    for cap in (
        "| 5.1 | `CBP_MAX_ORDER_NOTIONAL` for first live run | ≤ $25 USD |",
        "| 5.2 | `CBP_MAX_DAILY_NOTIONAL` for first live run | ≤ $50 USD |",
        "| 5.3 | `CBP_MAX_DAILY_LOSS` for first live run | ≤ $25 USD |",
        "| 5.4 | `CBP_MAX_TRADES_PER_DAY` for first live run | ≤ 5 |",
    ):
        assert cap in text

    for field in (
        "| Completed by | |",
        "| Date completed | |",
        "| Git commit at time of sign-off | |",
        "| First live notional cap confirmed | |",
        "| Branch pushed to origin | |",
    ):
        assert field in text
