import importlib

import pytest


@pytest.mark.parametrize(
    "module_path",
    [
        "services.governance.deployment_truth",
        "services.governance.campaign_state",
        "services.governance.campaign_fingerprint",
        "services.governance.campaign_state_machine",
        "services.governance.campaign_validation",
        "services.governance.invalidation",
        "services.governance.decision_engine",
        "services.governance.claims_guard",
        "services.governance.operator_overrides",
    ],
)
def test_governance_modules_exist(module_path):
    mod = importlib.import_module(module_path)
    assert mod is not None


def test_deployment_truth_get_mode():
    from services.governance.deployment_truth import get_deployment_mode

    assert get_deployment_mode() in {"local_private_only", "remote_public_candidate"}


def test_campaign_state_rejects_unknown():
    from services.governance.campaign_state import is_valid_campaign_state

    assert is_valid_campaign_state("INVALID") is True
    assert is_valid_campaign_state("HACKED_STATE") is False


def test_fingerprint_is_deterministic():
    from services.governance.campaign_fingerprint import generate_fingerprint

    data = {"a": 1, "b": 2}
    assert generate_fingerprint(data) == generate_fingerprint(data)


def test_invalid_transition_blocked():
    from services.governance.campaign_state_machine import can_transition

    assert can_transition("INVALID", "running") is False


def test_campaign_validation_rejects_missing_strategy():
    from services.governance.campaign_validation import validate_campaign_payload

    assert validate_campaign_payload({"foo": "bar"}) is False


def test_invalidation_triggers():
    from services.governance.invalidation import should_invalidate

    assert should_invalidate("drift") is True
    assert should_invalidate("random") is False


def test_decision_engine_blocks_invalid():
    from services.governance.decision_engine import decide

    assert decide("INVALID") == "BLOCK"


def test_claims_guard_rejects_bad_claims():
    from services.governance.claims_guard import validate_claim

    assert validate_claim({"content": "guaranteed profit"}) == "REJECTED"


def test_operator_override_blocks_risk_escalation():
    from services.governance.operator_overrides import apply_override

    with pytest.raises(ValueError):
        apply_override(
            {"risk": {"max_order_quote": 10.0}, "strategy": {"trade_enabled": True}},
            "balanced",
            overrides={"risk": {"max_order_quote": 10_000_000.0}},
        )

def test_fingerprint_changes_when_payload_changes():
    from services.governance.campaign_fingerprint import generate_fingerprint

    original = {"a": 1, "b": 2}
    mutated = {"a": 1, "b": 3}

    assert generate_fingerprint(original) != generate_fingerprint(mutated)

def test_operator_override_allows_safe_override():
    from services.governance.operator_overrides import apply_override
    from services.profiles.bundles import BUNDLES

    bundle_name = next(iter(BUNDLES.keys()))

    out = apply_override(
        {"risk": {"max_order_quote": 10.0}, "strategy": {"trade_enabled": True}},
        bundle_name,
        overrides={"risk": {"max_order_quote": 100.0}},
    )

    assert out["risk"]["max_order_quote"] == 100.0

def test_fingerprint_changes_when_payload_changes():
    from services.governance.campaign_fingerprint import generate_fingerprint

    original = {"a": 1, "b": 2}
    mutated = {"a": 1, "b": 3}

    assert generate_fingerprint(original) != generate_fingerprint(mutated)

def test_operator_override_allows_safe_override():
    from services.governance.operator_overrides import apply_override
    from services.profiles.bundles import BUNDLES

    bundle_name = next(iter(BUNDLES.keys()))

    out = apply_override(
        {"risk": {"max_order_quote": 10.0}, "strategy": {"trade_enabled": True}},
        bundle_name,
        overrides={"risk": {"max_order_quote": 100.0}},
    )

    assert out["risk"]["max_order_quote"] == 100.0
