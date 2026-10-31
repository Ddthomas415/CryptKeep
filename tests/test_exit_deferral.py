"""Synthetic-only exit planning. Existing execution callers are not modified."""

from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import socket

import pytest

from services.execution.exit_deferral import ExitPolicy, plan_exit


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def inputs():
    intent = {"intent_id": "exit-1", "venue": "coinbase", "product_id": "ETH-USD",
              "side": "sell", "order_type": "market", "quantity": "2", "limit_price": None,
              "opaque": {"original": [1, 2]}}
    observation = {"venue": "coinbase", "received_at_ms": 1000, "product": {
        "id": "ETH-USD", "status": "online", "trading_disabled": False,
        "cancel_only": False, "limit_only": False, "post_only": False, "auction_mode": False}}
    progress = {"intent_id": "exit-1", "venue": "coinbase", "product_id": "ETH-USD",
                "attempts": 0, "last_attempt_ms": None, "outcome": "never_submitted",
                "confirmed_filled_quantity": "0"}
    policy = ExitPolicy(max_metadata_age_ms=100, base_retry_ms=10, max_retry_ms=40, max_attempts=4)
    return intent, observation, progress, policy


def run(intent, observation, progress, policy, now=1000):
    return plan_exit(intent, observation, progress, now_ms=now, policy=policy)


@pytest.mark.parametrize("flag", ["cancel_only", "limit_only", "post_only", "auction_mode", "trading_disabled", "view_only"])
def test_restricted_market_exit_preserved_with_undelivered_alert(flag):
    intent, observation, progress, policy = inputs()
    observation["product"][flag] = True
    before = deepcopy((intent, observation, progress))
    result = run(intent, observation, progress, policy)
    assert result["status"] == "DEFER" and result["request"] is None
    assert result["intent"] == intent and result["progress"] == progress
    assert not result["execution_authority"] and not result["evidence_authenticated"]
    assert result["alert_event"]["delivery_verified"] is False
    assert result["next_check_ms"] == 1010
    result["intent"]["opaque"]["original"].append(3)
    assert (intent, observation, progress) == before


def test_existing_limit_exit_is_not_repriced_in_limit_only():
    intent, observation, progress, policy = inputs()
    intent.update(order_type="limit", limit_price="42.123")
    observation["product"]["limit_only"] = True
    result = run(intent, observation, progress, policy)
    assert result["status"] == "ELIGIBLE_FOR_EXISTING_GATES"
    assert result["intent"] == intent and result["request"] is None


@pytest.mark.parametrize("change, reason", [
    (lambda o: o.update(venue="other"), "metadata_unknown"),
    (lambda o: o.update(received_at_ms=899), "metadata_stale"),
    (lambda o: o.update(received_at_ms=1001), "metadata_clock_unknown"),
    (lambda o: o.update(received_at_ms=True), "metadata_clock_unknown"),
    (lambda o: o["product"].update(id="BTC-USD"), "metadata_product_mismatch"),
    (lambda o: o["product"].pop("limit_only"), "metadata_flags_unknown"),
    (lambda o: o["product"].update(cancel_only="false"), "metadata_flags_unknown"),
    (lambda o: o["product"].update(view_only="false"), "metadata_flags_unknown"),
    (lambda o: o["product"].update(status="offline"), "product_not_tradable"),
])
def test_unknown_stale_or_wrong_metadata_withholds(change, reason):
    intent, observation, progress, policy = inputs()
    change(observation)
    result = run(intent, observation, progress, policy)
    assert result["status"] == "DEFER" and result["reason"] == reason


@pytest.mark.parametrize("attempts, last, now, status, next_check", [
    (1, 990, 999, "DEFER", 1000), (1, 990, 1000, "ELIGIBLE_FOR_EXISTING_GATES", None),
    (2, 980, 999, "DEFER", 1000), (3, 960, 999, "DEFER", 1000),
    (4, 990, 1000, "NEEDS_OPERATOR", None),
])
def test_explicit_attempt_and_backoff_bounds(attempts, last, now, status, next_check):
    intent, observation, progress, policy = inputs()
    observation["received_at_ms"] = now
    progress.update(attempts=attempts, last_attempt_ms=last, outcome="rejected")
    result = run(intent, observation, progress, policy, now)
    assert result["status"] == status and result["next_check_ms"] == next_check
    assert result["progress"] == progress  # Planning is not a counted submit.


@pytest.mark.parametrize("outcome", ["open", "unknown"])
def test_unresolved_order_never_retries_even_after_budget_or_metadata_recovers(outcome):
    intent, observation, progress, policy = inputs()
    progress.update(attempts=4, last_attempt_ms=900, outcome=outcome, confirmed_filled_quantity="0.5")
    result = run(intent, observation, progress, policy)
    assert result["status"] == "RECONCILE" and result["request"] is None
    assert result["remaining_units"] == [3, 2]


def test_cancelled_partial_fill_reassesses_only_exact_confirmed_remainder():
    intent, observation, progress, policy = inputs()
    intent["quantity"] = "1.000000000000000000000000000001"
    progress.update(attempts=1, last_attempt_ms=980, outcome="cancelled", confirmed_filled_quantity="1")
    result = run(intent, observation, progress, policy)
    assert result["status"] == "ELIGIBLE_FOR_EXISTING_GATES"
    assert Fraction(*result["remaining_units"]) == Fraction(1, 10**30)
    assert result["intent"]["quantity"] == intent["quantity"]


@pytest.mark.parametrize("outcome, status", [("filled", "COMPLETE"), ("cancelled", "RECONCILE")])
def test_full_quantity_requires_terminal_fill_confirmation(outcome, status):
    intent, observation, progress, policy = inputs()
    progress.update(attempts=1, last_attempt_ms=980, outcome=outcome, confirmed_filled_quantity="2")
    assert run(intent, observation, progress, policy)["status"] == status


@pytest.mark.parametrize("kwargs", [dict(max_attempts=0), dict(base_retry_ms=True),
                                   dict(max_metadata_age_ms=0), dict(max_retry_ms=1)])
def test_policy_has_no_permissive_missing_or_invalid_defaults(kwargs):
    values = dict(max_metadata_age_ms=100, base_retry_ms=10, max_retry_ms=40, max_attempts=4)
    values.update(kwargs)
    with pytest.raises(ValueError):
        ExitPolicy(**values)
    with pytest.raises(TypeError):
        ExitPolicy()


@pytest.mark.parametrize("change", [
    lambda i, p: i.update(side="buy"), lambda i, p: i.update(quantity="NaN"),
    lambda i, p: i.update(quantity=True), lambda i, p: p.update(attempts=True),
    lambda i, p: p.update(confirmed_filled_quantity="3"),
    lambda i, p: p.update(attempts=1, last_attempt_ms=1001, outcome="rejected"),
    lambda i, p: p.update(outcome="unknown"),
    lambda i, p: p.update(intent_id="different-exit"),
    lambda i, p: p.update(venue="different-venue"),
    lambda i, p: p.update(product_id="BTC-USD"),
])
def test_inconsistent_inputs_cannot_produce_an_eligible_result(change):
    intent, observation, progress, policy = inputs()
    change(intent, progress)
    with pytest.raises(ValueError):
        run(intent, observation, progress, policy)


def test_caller_bound_exponent_and_metadata_age_boundary():
    intent, observation, progress, _ = inputs()
    policy = ExitPolicy(100, 10, 40, 10**100)
    progress.update(attempts=10**90, last_attempt_ms=960, outcome="rejected")
    observation["received_at_ms"] = 900
    assert run(intent, observation, progress, policy)["status"] == "ELIGIBLE_FOR_EXISTING_GATES"
