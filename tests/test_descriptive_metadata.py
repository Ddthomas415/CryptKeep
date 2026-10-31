"""Invented metadata and prices only; no historical eligibility or returns."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import socket
import subprocess

import pytest

from services.backtest import descriptive_metadata as metadata
from services.backtest import shared_cash_research as ledger


H = metadata.HOUR


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("metadata test attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, refuse)


def identity(symbol="A"):
    return {"product_id": symbol + "-USD", "base_currency": symbol, "quote_currency": "USD",
            "identity_evidence_sha256": hashlib.sha256(("invented identity " + symbol).encode()).hexdigest()}


def product(symbol="A", **changes):
    return {"id": symbol + "-USD", "base_currency": symbol, "quote_currency": "USD",
            "status": "online", "base_increment": "0.001", "quote_increment": "0.00001",
            **dict.fromkeys(metadata.FLAGS, False), **changes}


def capture(received=100, products=None, raw=None):
    return {"received_at_ms": received, "products_bytes": raw if raw is not None else
            json.dumps([product()] if products is None else products).encode()}


def mapped(captures=None, identities=None):
    return metadata.map_public_metadata([capture()] if captures is None else captures,
        identities={"A": identity()} if identities is None else identities)


def at(result, decision=100, execution=None, symbol="A"):
    return ledger.rule_at(result["rules"], symbol, decision,
        decision if execution is None else execution, "coinbase", "USD")


def test_exact_rule_hash_precision_minima_and_no_input_mutation():
    snapshots, identities = [capture()], {"A": identity()}
    before = deepcopy((snapshots, identities))
    result = mapped(snapshots, identities)
    row = at(result)
    assert row["eligible"] and row["lot_step"] == F(1, 1000)
    assert row["quote_step"] == F(1, 100)  # Not the product price tick.
    assert row["minimum_qty"] == row["minimum_notional_gross"] == 0
    assert row["source_sha256"] == hashlib.sha256(snapshots[0]["products_bytes"]).hexdigest()
    assert (snapshots, identities) == before and not result["identity_authenticity_verified"]
    assert "view_only" not in result["observations"][0]["observed_flags"]


def test_receipt_never_applies_backwards_and_expiry_is_exclusive():
    result = mapped()
    assert at(result, 100 + H - 1)["eligible"]
    for decision, execution in ((99, 100), (100, 99), (100, 100 + H), (100 + H, 100 + H)):
        with pytest.raises(ledger.Incomplete):
            at(result, decision, execution)


@pytest.mark.parametrize("flag", metadata.FLAGS + ("view_only",))
def test_each_restrictive_flag_blocks(flag):
    result = mapped([capture(products=[product(**{flag: True})])])
    assert at(result)["eligible"] is False
    assert result["observations"][0]["reason"] == "known_ineligible"


@pytest.mark.parametrize("flag", metadata.FLAGS)
@pytest.mark.parametrize("bad", [None, 0, "false"])
def test_flags_are_explicit_booleans_not_truthy_defaults(flag, bad):
    result = mapped([capture(products=[product(**{flag: bad})])])
    with pytest.raises(ledger.Incomplete):
        at(result)


def test_missing_required_flag_is_unknown_even_on_delisted_product():
    p = product(status="delisted")
    del p["cancel_only"]
    result = mapped([capture(products=[p])])
    assert result["observations"][0]["status"] == "INCOMPLETE"
    with pytest.raises(ledger.Incomplete):
        at(result)


@pytest.mark.parametrize("changes", [{"base_currency": "OTHER"}, {"quote_currency": "EUR"},
    {"base_increment": "0"}, {"base_increment": "NaN"}, {"base_increment": True},
    {"status": None}, {"view_only": "false"}])
def test_invalid_identity_status_or_precision_is_unknown(changes):
    result = mapped([capture(products=[product(**changes)])])
    assert result["observations"][0]["eligible"] is None
    with pytest.raises(ledger.Incomplete):
        at(result)


@pytest.mark.parametrize("raw", [b"broken", b'{}', b'[null]', b'[{"id":"A-USD","id":"A-USD"}]',
                                  b'[{"x":NaN}]', b'\xff'])
def test_bad_payload_keeps_an_unknown_barrier_for_every_symbol(raw):
    result = mapped([capture(raw=raw)], {"A": identity(), "B": identity("B")})
    assert len(result["observations"]) == 2
    for symbol in result["rules"]:
        with pytest.raises(ledger.Incomplete):
            at(result, symbol=symbol)


@pytest.mark.parametrize("products", [[], [product(), product()]])
def test_missing_or_duplicate_product_never_chooses_a_match(products):
    with pytest.raises(ledger.Incomplete):
        at(mapped([capture(products=products)]))


def test_latest_unknown_shadows_still_valid_old_permission_then_can_recover():
    result = mapped([capture(), capture(200, raw=b"bad"), capture(300)])
    assert at(result, 199)["eligible"]
    with pytest.raises(ledger.Incomplete):
        at(result, 200)
    with pytest.raises(ledger.Incomplete):
        at(result, 250, 300)  # Future recovery was not known at decision time.
    assert at(result, 300)["eligible"]


def test_signal_and_execution_permissions_use_their_separate_receipts():
    result = mapped([capture(), capture(200, products=[product(cancel_only=True)])])
    assert at(result, 150)["eligible"]
    assert not at(result, 200)["eligible"]


def test_unresolved_identity_stays_in_denominator_and_no_ticker_substitution():
    result = mapped([capture(products=[product("POL")])], {"MATIC": identity("MATIC"), "B": None})
    assert set(result["rules"]) == {"MATIC", "B"}
    assert all(r["eligible"] is None for r in result["observations"])


@pytest.mark.parametrize("received", [-1, True, 1.5, None])
def test_invalid_receipt_is_refused_not_repaired(received):
    with pytest.raises(ValueError):
        mapped([capture(received)])


def test_ambiguous_receipts_and_shared_product_assignment_are_refused():
    with pytest.raises(ValueError, match="ambiguous_receipt"):
        mapped([capture(), capture()])
    with pytest.raises(ValueError, match="duplicate_product_assignment"):
        mapped(identities={"A": identity(), "B": identity()})


def test_all_25_synthetic_identities_feed_existing_seven_arm_comparison_and_carry(monkeypatch):
    from services.backtest import delayed_research_comparison as comparison
    from services.backtest import frozen_signal_bridge as frozen

    symbols = tuple("TEST%02d" % i for i in range(25))
    ids = {s: identity(s) for s in symbols}
    products = [product(s) for s in symbols]
    rules = mapped([capture(i * H - 1, products=products) for i in range(300, 308)], ids)["rules"]
    observations = {s: [{"row": [i*H, 100, 102, 98, 100, 1000], "known_at_ms": (i+1)*H+1}
                       for i in range(307)] for s in symbols}
    frames = [{"ts_ms": i*H, "open": dict.fromkeys(symbols, 100), "close": dict.fromkeys(symbols, 100)}
              for i in range(300, 307)]
    monkeypatch.setattr(frozen, "compute_signal", lambda **kwargs: {"ok": True, "action": "hold"})
    snapshot = (Path(__file__).resolve().parents[1] /
                "research/multisymbol_baseline_v1/strategies.snapshot.json").read_bytes()
    profile = dict(symbols=symbols, observations=observations, rules=rules, venue="coinbase", quote="USD",
        snapshot_bytes=snapshot, btc_symbol=symbols[0], eth_symbol=symbols[1],
        mix_weights={symbols[0]: F(1,4), symbols[1]: F(1,4)}, evaluation_start_ms=300*H,
        evaluation_end_ms=307*H, initial_cash=1000, fee_bps=50, slippage_bps=25,
        target_contract_id="synthetic-metadata-integration")
    whole = comparison.simulate_delayed_comparison(frames, **profile)
    first = comparison.simulate_delayed_comparison(frames[:4], **profile)
    resumed = comparison.simulate_delayed_comparison(frames[4:], states=first["states"], **profile)
    assert whole["economic_result_usable"] and resumed["economic_result_usable"]
    assert whole["states"] == resumed["states"]
    assert set(whole["arms"]) == set(comparison.ARM_NAMES)
    assert all(set(a["state"]["units"]) == set(symbols) for a in whole["arms"].values())
