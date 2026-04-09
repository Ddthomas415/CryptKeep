from pathlib import Path


DOC = Path("docs/governance/governance_signoff.md")


def test_governance_signoff_has_no_tbd_placeholders() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "| TBD |" not in text


def test_governance_signoff_references_canonical_governance_wrappers() -> None:
    text = DOC.read_text(encoding="utf-8")

    expected = [
        "`services/governance/deployment_truth.py`",
        "`services/governance/campaign_state.py`",
        "`services/governance/campaign_state_machine.py`",
        "`services/governance/campaign_validation.py`",
        "`services/governance/invalidation.py`",
        "`services/governance/decision_engine.py`",
        "`services/governance/claims_guard.py`",
        "`services/governance/operator_overrides.py`",
    ]

    for needle in expected:
        assert needle in text
