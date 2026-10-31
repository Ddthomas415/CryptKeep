"""Synthetic arithmetic/causality fixtures, not confidence-coverage evidence."""
from copy import deepcopy
import math
import socket
import subprocess

import numpy as np
import pytest

from services.backtest import paired_wealth_screen as screen


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic statistics attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbidden)


def panel(returns=None):
    returns = {} if returns is None else returns
    return {arm: [{"day_end_ms": (i+1)*screen.DAY, "return": float(values[i])}
            for i in range(screen.DAYS)]
            for arm in screen.ARMS for values in [returns.get(arm, np.zeros(screen.DAYS))]}


def test_null_identical_arms_are_exactly_paired_not_a_claim_of_coverage():
    values = np.sin(np.arange(screen.DAYS)/11)*.01
    data = panel(dict.fromkeys(screen.ARMS, values))
    original = deepcopy(data)
    result = screen.paired_wealth_screen(data, initial_cash=1000)
    assert result["computation_status"] == "COMPLETE" and data == original
    assert result["one_based_order_rank"] == 334 and result["repeats"] == 20000
    assert result["statistical_validation"] == "INCOMPLETE" and not result["coverage_certified"]
    assert result["experiment_pass"] is None
    for contrast in result["contrasts"].values():
        assert contrast["observed_net_wealth_difference"] == 0
        assert contrast["approximate_lower_bound"] == 0 and not contrast["lower_bound_exceeds_zero"]


@pytest.mark.parametrize("effect", [.001, -.001])
def test_constant_known_effect_recompounds_not_sum_of_returns(effect):
    data = panel({name: np.full(screen.DAYS, effect) for name in screen.FAMILIES})
    result = screen.paired_wealth_screen(data, initial_cash=1000)
    expected = 1000*math.expm1(screen.DAYS*math.log1p(effect))
    for contrast in result["contrasts"].values():
        assert contrast["observed_net_wealth_difference"] == pytest.approx(expected)
        assert contrast["approximate_lower_bound"] == pytest.approx(expected)
        assert contrast["lower_bound_exceeds_zero"] is (effect > 0)


def test_first_day_entry_cost_is_not_rebased_away():
    values = np.zeros(screen.DAYS)
    values[0] = -.01
    result = screen.paired_wealth_screen(panel(dict.fromkeys(screen.FAMILIES, values)), initial_cash=1000)
    assert result["contrasts"][screen.FAMILIES[0]]["observed_net_wealth_difference"] == pytest.approx(-10)


def test_circular_blocks_wrap_preserve_order_and_truncate():
    starts = np.full((1, math.ceil(screen.DAYS/7)), 180, dtype=np.int64)
    indices = screen.circular_indices(starts, 7)
    assert indices.shape == (1, 182)
    assert indices[0, :7].tolist() == [180, 181, 0, 1, 2, 3, 4]
    assert indices[0, -7:].tolist() == [180, 181, 0, 1, 2, 3, 4]


def test_rank_matches_inverted_cdf_without_interpolation():
    values = np.arange(screen.REPEATS, dtype=float)
    assert np.quantile(values, 1/60, method="inverted_cdf") == values[(screen.REPEATS+59)//60-1]


def test_serial_dependence_preserves_joint_pairing_and_fixed_seed():
    rng = np.random.Generator(np.random.PCG64(901))
    values = np.zeros(screen.DAYS)
    for i in range(1, screen.DAYS):
        values[i] = .8*values[i-1]+rng.normal(0, .003)
    data = panel(dict.fromkeys(screen.ARMS, values))
    a = screen.paired_wealth_screen(data, initial_cash=1000)
    b = screen.paired_wealth_screen(data, initial_cash=1000)
    assert a == b
    assert all(v["approximate_lower_bound"] == 0 for v in a["contrasts"].values())


@pytest.mark.parametrize("block", [14, 28])
def test_sensitivities_are_labelled_not_selected_as_primary(block):
    r = screen.paired_wealth_screen(panel(), initial_cash=1000, block_days=block)
    assert r["computation_status"] == "COMPLETE" and r["primary_method"] is False


@pytest.mark.parametrize("fault", ["missing_arm", "short", "misaligned", "gap", "duplicate",
                                   "nan", "infinity", "below_loss_limit", "bool", "extra_field"])
def test_invalid_daily_inputs_refused(fault):
    data = panel()
    arm = screen.FAMILIES[0]
    if fault == "missing_arm":
        data.pop("cash")
    elif fault == "short":
        data[arm].pop()
    elif fault == "misaligned":
        for row in data[arm]: row["day_end_ms"] += screen.DAY
    elif fault == "gap":
        data[arm][50]["day_end_ms"] += screen.DAY
    elif fault == "duplicate":
        data[arm][50]["day_end_ms"] -= screen.DAY
    elif fault == "extra_field":
        data[arm][0]["source"] = "not-the-declared-schema"
    else:
        data[arm][0]["return"] = {"nan": float("nan"), "infinity": float("inf"),
                                  "below_loss_limit": -1.01, "bool": True}[fault]
    with pytest.raises(ValueError):
        screen.paired_wealth_screen(data, initial_cash=1000)


@pytest.mark.parametrize("capital", [True, 0, 999, 1001, float("nan")])
def test_unadopted_capital_or_invalid_value_refused(capital):
    with pytest.raises(ValueError):
        screen.paired_wealth_screen(panel(), initial_cash=capital)


def test_exhaustion_is_zero_wealth_but_not_a_sharpe_error():
    values = np.zeros(screen.DAYS)
    values[0] = -1
    result = screen.paired_wealth_screen(panel(dict.fromkeys(screen.FAMILIES, values)), initial_cash=1000)
    assert result["computation_status"] == "COMPLETE"
    assert result["contrasts"][screen.FAMILIES[0]]["observed_net_wealth_difference"] == -1000
    values[1] = .1
    with pytest.raises(ValueError, match="after_exhaustion"):
        screen.paired_wealth_screen(panel(dict.fromkeys(screen.FAMILIES, values)), initial_cash=1000)


def test_numerical_failure_cannot_drop_replicates_or_make_a_pass():
    data = panel({screen.FAMILIES[0]: np.full(screen.DAYS, 100.)})
    result = screen.paired_wealth_screen(data, initial_cash=1000)
    assert result["computation_status"] == "INCOMPLETE" and result["contrasts"] is None
    assert result["experiment_pass"] is None


def test_known_resampling_indices_recompose_exact_block_sequence(monkeypatch):
    class FixedStarts:
        def integers(self, low, high, *, size, dtype):
            return np.zeros(size, dtype=dtype)
    monkeypatch.setattr(np.random, "Generator", lambda bit_generator: FixedStarts())
    values = np.arange(screen.DAYS)*.00001
    result = screen.paired_wealth_screen(panel(dict.fromkeys(screen.FAMILIES, values)), initial_cash=1000)
    expected = 1000*math.expm1(26*sum(math.log1p(v) for v in values[:7]))
    assert result["contrasts"][screen.FAMILIES[0]]["approximate_lower_bound"] == pytest.approx(expected)


def test_resample_only_overflow_does_not_drop_bad_draws():
    values = np.zeros(screen.DAYS)
    values[0] = 1e300
    result = screen.paired_wealth_screen(panel({screen.FAMILIES[0]: values}), initial_cash=1000)
    assert result["computation_status"] == "INCOMPLETE" and result["contrasts"] is None
    assert result["reason"] == "unrepresentable_wealth_no_replicates_dropped"
