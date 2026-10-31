"""Deterministic runner helpers only: never invoke the development stage."""
import importlib.util
from pathlib import Path
import socket
import subprocess

import numpy as np
import pytest


SCRIPT = Path(__file__).resolve().parents[1]/"docs/research/ed002_sb1_development_20261027/run_development.py"
spec = importlib.util.spec_from_file_location("sb1_development_helpers", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture(autouse=True)
def no_random_stage(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("helper test attempted random stage or external work")
    for name in ("Generator", "PCG64", "default_rng"):
        monkeypatch.setattr(np.random, name, forbidden)
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call"):
        monkeypatch.setattr(subprocess, name, forbidden)


def test_stage_budget_and_cases_are_exact():
    assert runner.TRIALS == 16 and len(runner.CASES) == 6
    assert runner.COMPUTE_SECONDS == 90 and runner.BURN == 1024
    assert runner.DOMAIN == "ED002-SB1-development-20261027"
    assert [rho for _, rho in runner.CASES] == [0., .5, .8, .95, -.5, None]


def test_stream_domains_reproducible_and_separated_without_rng():
    a = runner.seed_hex("frozen-id", "iid_gaussian", 0, "data")
    assert a == runner.seed_hex("frozen-id", "iid_gaussian", 0, "data")
    assert len({a, runner.seed_hex("frozen-id", "iid_gaussian", 0, "draws"),
        runner.seed_hex("frozen-id", "iid_gaussian", 1, "data"),
        runner.seed_hex("other-id", "iid_gaussian", 0, "data")}) == 4


def test_gaussian_recurrence_with_known_initial_state():
    innovations = np.zeros((5, 2))
    initial = np.array([1., 2.])
    actual = runner.gaussian_factors(innovations, initial, .5)
    expected = np.array([initial*.5**i for i in range(5)])
    assert np.array_equal(actual, expected)
    innovations[1:] = 1.
    actual = runner.gaussian_factors(innovations, initial, 0.)
    assert np.array_equal(actual[0], initial) and np.all(actual[1:] == 1.)


def test_volatility_state_persistence_threshold_and_initial_state():
    uniforms = np.array([.94, .95, .1, .99])
    assert np.array_equal(runner.volatility_scales(uniforms, 0), [.5, .5, 2., 2., .5])
    assert np.array_equal(runner.volatility_scales(uniforms, 1), [2., 2., .5, .5, 2.])


def test_four_null_arms_use_identical_formula_and_cash_is_zero():
    factors = np.zeros((182, 5))
    factors[:, 0] = .2
    factors[:, 1:] = .3
    values = runner.null_returns(factors)
    assert values.shape == (182, 7) and np.all(values[:, 4] == 0)
    assert np.all(values[:, :4] == np.expm1(.01*.2+.005*.3))
    assert np.all(values[:, 6] == .5*values[:, 5])


def test_summary_keeps_abstentions_separate_from_computed_negatives():
    complete = {"computation_status": "COMPLETE", "contrasts": {"x": {"lower_bound_exceeds_zero": True}}}
    abstained = {"computation_status": "INCOMPLETE", "reason": "insufficient_effective_blocks"}
    rows = [{"case": "x", "method_result": complete}, {"case": "x", "method_result": abstained}]
    result = runner.summarize(rows, "x", {"case": "x"})
    assert result["completed_trials"] == 2 and result["computable_trials"] == 1
    assert result["familywise_positive_count"] == 1 and result["abstentions_or_failures"] == 1
    assert result["unconditional_positive_rate"] == .5 and result["conditional_positive_rate"] == 1.
    assert result["interrupted_trials"] == 1 and result["unattempted_trials"] == 13
    assert runner.summarize([], "x")["conditional_positive_rate"] is None


def test_no_audit_argument_can_silently_start_development(monkeypatch):
    monkeypatch.setattr(runner.sys, "argv", [str(SCRIPT), "--audit"])
    with pytest.raises(ValueError, match="no_arguments_or_audit"):
        runner.main()


def test_existing_attempt_is_preserved_before_any_action(monkeypatch, tmp_path):
    marker = tmp_path/"ATTEMPT.json"
    marker.write_text("preserve")
    monkeypatch.setattr(runner, "HERE", tmp_path)
    monkeypatch.setattr(runner.sys, "argv", [str(SCRIPT)])
    with pytest.raises(FileExistsError):
        runner.main()
    assert marker.read_text() == "preserve" and len(list(tmp_path.iterdir())) == 1
