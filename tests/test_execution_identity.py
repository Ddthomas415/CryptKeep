import copy

import pytest

from services.strategies.execution_identity import (
    fill_identity_evidence, identity_evidence, identity_rejection_reasons,
)


def payload():
    return {
        "version": 1, "cohort_id": "synthetic-cohort", "strategy_name": "sma_200_trend",
        "parameters": {"sma_period": 200, "atr_period": 20},
        "entry_policy": {"rule": "completed_daily_crossover", "allow_first": False},
        "exit_policy": {"rule": "close_below_sma", "trailing_stop_pct": 0.0},
        "sizing": {"qty": 0.001, "sell_full_position": True},
        "costs": {"fee_bps": 7.5, "slippage_bps": 5.0, "quote_currency": "USDT", "basis_version": "both_fees_v1"},
        "market": {"venue": "coinbase", "symbol": "BTC/USDT", "timeframe": "1d", "source": "public_ohlcv", "sample_mode": False},
        "implementation": {key: "a" * 64 for key in ("signal", "resolver", "exits", "paper_engine")},
    }


def test_canonical_order_and_detached_payload():
    original = payload()
    evidence = identity_evidence(original)
    assert evidence == identity_evidence(dict(reversed(list(original.items()))))
    original["parameters"]["sma_period"] = 20
    assert evidence["execution_identity"]["parameters"]["sma_period"] == 200


@pytest.mark.parametrize("section,key,value", [
    ("parameters", "sma_period", 20), ("exit_policy", "trailing_stop_pct", 0.02),
    ("costs", "fee_bps", 50.0), ("costs", "basis_version", "sell_fee_only"),
    ("sizing", "qty", 1.0), ("market", "symbol", "BTC/USD"),
    ("implementation", "signal", "b" * 64),
])
def test_policy_change_rejected(section, key, value):
    expected = identity_evidence(payload())["execution_identity_sha256"]
    changed = payload()
    changed[section][key] = value
    assert identity_rejection_reasons(identity_evidence(changed), expected_sha256=expected) == ["execution_identity_mismatch"]


def test_missing_and_contradictory_identity_rejected():
    evidence = identity_evidence(payload())
    digest = evidence["execution_identity_sha256"]
    assert identity_rejection_reasons({}, expected_sha256=digest) == ["missing_execution_identity"]
    evidence["execution_identity"]["parameters"]["sma_period"] = 20
    assert identity_rejection_reasons(evidence, expected_sha256=digest) == ["execution_identity_content_mismatch"]
    assert identity_rejection_reasons({}, expected_sha256="") == ["invalid_expected_execution_identity"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "7.5"])
def test_invalid_costs_rejected(value):
    changed = payload()
    changed["costs"]["fee_bps"] = value
    with pytest.raises(ValueError):
        identity_evidence(changed)


def test_schema_is_strict():
    for key in payload():
        changed = payload()
        del changed[key]
        with pytest.raises(ValueError):
            identity_evidence(changed)
    changed = payload()
    changed["credential"] = "not-allowed"
    with pytest.raises(ValueError):
        identity_evidence(changed)


def test_intent_to_fill_copy_verifies_effective_costs():
    original = payload()
    intent = identity_evidence(original)
    result = fill_identity_evidence(intent, effective_costs=copy.deepcopy(original["costs"]))
    assert result == intent
    intent["execution_identity"]["parameters"]["sma_period"] = 20
    assert result["execution_identity"]["parameters"]["sma_period"] == 200
    with pytest.raises(ValueError, match="content_mismatch"):
        fill_identity_evidence(intent, effective_costs=original["costs"])
    changed_costs = {**original["costs"], "fee_bps": 50.0}
    with pytest.raises(ValueError, match="cost_mismatch"):
        fill_identity_evidence(identity_evidence(original), effective_costs=changed_costs)
