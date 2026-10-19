"""Synthetic-only regressions; no archives, services, credentials or markets."""
import ast
import copy
import hashlib
from pathlib import Path

import pytest

from scripts.research import module_a_candidate as candidate
from scripts.research.corrected_research_math import rebalance


def _sale_case(close=100.0, module=candidate, trace=None):
    kwargs = {} if trace is None else {"trace": trace}
    return module.simulate({"A": [100.0] * 3}, {"A": [100.0, 100.0, close]},
                           [0, 6, 0], 0, 2, lambda i: {"A": 1.0} if i == 0 else {},
                           0.0, 0.0, cash0=100.0, **kwargs)


def test_original_counterexample_is_preserved_and_reproduced():
    path = Path(__file__).resolve().parents[1] / (
        "docs/review_artifacts/information_edge_repair_20261018/original_module_a_sim.py.txt")
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "2be805171d14b37b232197974bc45de95fa289db528172990fe52bebb6896f12"
    # Resolve only the draft's unqualified helper import; financial code unchanged.
    tree = ast.parse(raw)
    imports = [n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == "corrected_research_math"]
    assert len(imports) == 1
    imports[0].module = "scripts.research.corrected_research_math"
    namespace = {}
    exec(compile(tree, str(path), "exec"), namespace)
    legacy = type("Legacy", (), {"simulate": staticmethod(namespace["simulate"])})
    assert _sale_case(module=legacy)[0][-1] == pytest.approx(100)
    assert _sale_case(close=None, module=legacy)[0][-1] == pytest.approx(50)


def test_missing_future_close_cannot_change_opening_sale_or_cash():
    complete, missing = [], []
    assert _sale_case(trace=complete) == _sale_case(close=None, trace=missing)
    assert complete == missing
    assert [r for r in missing if r["phase"] == "open"][-1]["cash"] == pytest.approx(100)
    assert all(r["evidence"] == "MODELLED" for r in missing)


@pytest.mark.parametrize("missing", [None, float("nan"), 0, -1])
def test_missing_held_close_stops_after_identical_open_without_recovery(missing):
    good, bad = [], []
    common = ({"A": [100.0] * 3}, [0] * 3, lambda i: {"A": 1.0})
    candidate.simulate(common[0], {"A": [100.0] * 3}, common[1], 0, 2, common[2], 0, 0,
                       cash0=100, trace=good)
    with pytest.raises(candidate.IncompleteSimulation) as error:
        candidate.simulate(common[0], {"A": [100.0, 100.0, missing]}, common[1], 0, 2,
                           common[2], 0, 0, cash0=100, trace=bad)
    assert (error.value.day, error.value.phase, error.value.cash) == (2, "close", 0)
    assert error.value.units == {"A": pytest.approx(1)}
    assert bad == good[:-1]


@pytest.mark.parametrize("asset", ["A", "B"])
def test_missing_execution_price_does_not_drop_holding_or_requested_buy(asset):
    opens = {"A": [100.0] * 3, "B": [100.0] * 3}
    opens[asset][2] = None
    trace = []
    with pytest.raises(candidate.IncompleteSimulation) as error:
        candidate.simulate(opens, {"A": [100.0] * 3, "B": [100.0] * 3}, [0, 6, 0], 0, 2,
                           lambda i: {"A" if i == 0 else "B": 1.0}, 0, 0, cash0=100, trace=trace)
    assert error.value.phase == "open" and error.value.asset == asset
    assert error.value.cash == 0 and error.value.units == {"A": pytest.approx(1)}
    assert not any(r["day"] == 2 for r in trace)


@pytest.mark.parametrize("recovery", [0, 0.5])
def test_undated_recovery_scenarios_are_not_silently_accepted(recovery):
    with pytest.raises(ValueError, match="separately frozen"):
        candidate.simulate({"A": [100.0] * 2}, {"A": [100.0] * 2}, [0, 0], 0, 1,
                           lambda i: {}, 0, 0, recovery=recovery)


@pytest.mark.parametrize("fee,slip", [(0, 0), (0.005, 0.0005), (0.012, 0.0005)])
def test_shared_helper_parity_and_sells_first_cash_at_every_step(fee, slip):
    opens = {"A": [100, 100, 120, 90], "B": [100, 200, 180, 220]}
    targets = [{"A": 0.9}, {"B": 0.9}, {}]
    trace = []
    candidate.simulate(opens, copy.deepcopy(opens), [0, 6, 6, 0], 0, 3,
                       lambda i: targets[i], fee, slip, cash0=1000, trace=trace)
    cash, units = 1000.0, {}
    for day, weights in enumerate(targets, 1):
        prices = {a: opens[a][day] for a in set(units) | set(weights)}
        cash, units = rebalance(cash, units, prices, weights, fee, slip)
        units = {a: q for a, q in units.items() if q > 0}
        opening = next(r for r in trace if r["phase"] == "open" and r["day"] == day)
        assert opening["cash"] == pytest.approx(cash, abs=1e-6)
        assert opening["units"] == pytest.approx(units, abs=1e-9)
        fills = [r for r in trace if r["phase"] == "fill" and r["day"] == day]
        assert [r["quantity"] >= 0 for r in fills] == sorted(r["quantity"] >= 0 for r in fills)
        assert all(r["cash_before"] >= -1e-7 and r["cash_after"] >= -1e-7 for r in fills)


def test_positive_nav_does_not_hide_negative_cash(monkeypatch):
    monkeypatch.setattr(candidate, "rebalance", lambda *args: (-100.0, {"A": 2.0}))
    with pytest.raises(ValueError, match="unaffordable"):
        candidate.simulate({"A": [100.0] * 2}, {"A": [100.0] * 2}, [0, 0], 0, 1,
                           lambda i: {"A": 1.0}, 0, 0, cash0=100)


def test_omitted_fee_is_detected_even_with_nonnegative_cash(monkeypatch):
    monkeypatch.setattr(candidate, "rebalance", lambda c, u, p, w, f, s: rebalance(c, u, p, w, 0, 0))
    with pytest.raises(ValueError, match="does not reconcile"):
        candidate.simulate({"A": [100.0] * 2}, {"A": [100.0] * 2}, [0, 0], 0, 1,
                           lambda i: {"A": 0.5}, 0.005, 0.0005, cash0=100)


def test_hand_calculated_round_trip_and_turnover():
    trace = []
    navs, turnover, _ = candidate.simulate({"A": [100, 100, 120]}, {"A": [100, 100, 120]},
                                         [0, 6, 0], 0, 2,
                                         lambda i: {"A": 1.0} if i == 0 else {},
                                         0.005, 0, cash0=1000, trace=trace)
    quantity = 1000 / (100 * 1.005)
    proceeds = quantity * 120 * 0.995
    assert navs[-1] == pytest.approx(proceeds)
    assert trace[-1]["cash"] == pytest.approx(proceeds)
    assert turnover == pytest.approx((1 / 1.005 + 1) / (2 / 365))


def test_target_and_nav_prefix_causality_and_leaky_canary():
    closes = {"A": [100 + i % 5 for i in range(20)]}
    altered = copy.deepcopy(closes)
    altered["A"][11:] = [200 + i for i in range(9)]
    opens = {"A": [100] * 20}
    weekday = [6] * 20

    def run(data, leaky=False):
        return candidate.simulate(opens, data, weekday, 0, 19,
                                  lambda i: {"A": data["A"][i + int(leaky)] / 1000},
                                  0.005, 0.0005, cash0=1000)
    a, b = run(closes), run(altered)
    assert a[0][:10] == b[0][:10]
    assert a[2][:11] == b[2][:11]
    assert run(closes, True)[2][10] != run(altered, True)[2][10]


def test_original_weight_and_volatility_conventions():
    assert candidate.capped_weights({"A": 4, "B": 2, "C": 1, "D": 1}, 0.3) == pytest.approx(
        {"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2})
    assert candidate.trailing_vol([100] * 5, 4, 4) == 0
    assert candidate.trailing_vol([100, None, 101], 2, 2) is None
    assert candidate.module_a_target({"A": [100, 101, 99]}, 2, ["A"], lookback=2) == {"A": 0.3}


@pytest.mark.parametrize("weights", [{"A": -1}, {"A": float("nan")}, {"A": 1.1}, {"B": 1}])
def test_invalid_targets_refuse(weights):
    with pytest.raises(ValueError):
        candidate.simulate({"A": [100] * 2}, {"A": [100] * 2}, [0, 0], 0, 1,
                           lambda i: weights, 0, 0)


def _allocator_prefix_case(*, future_changed=False, leaky=False, daily=False):
    import math
    import random

    rng = random.Random(31)
    opens, closes = {}, {}
    for index in range(4):
        asset, price = f"A{index}", 80 + 20 * index
        opens[asset], closes[asset] = [], []
        for _ in range(30):
            opens[asset].append(price * (1 + rng.uniform(-0.01, 0.01)))
            price *= math.exp(rng.gauss(0, 0.01 + 0.01 * index))
            closes[asset].append(price)
    cutoff, start = 12, 4
    if future_changed:
        future = random.Random(99)
        for asset in opens:
            for day in range(cutoff + 1, 30):
                opens[asset][day] = future.uniform(30, 300)
                closes[asset][day] = future.uniform(30, 300)
    # Both schedules decide at cutoff12; weekly mode also exercises Sunday timing.
    weekdays = [6] * 30 if daily else [(day + 1) % 7 for day in range(30)]
    trace = []
    result = candidate.simulate(
        opens, closes, weekdays, start, 29,
        lambda day: candidate.module_a_target(
            closes, day + int(leaky), sorted(closes), lookback=4, cap=0.30, min_assets=4),
        fee=0.012, slip=0.0005, cash0=1000, trace=trace)
    return result, trace, start, cutoff


@pytest.mark.parametrize("daily", [False, True], ids=["weekly", "daily_fixture"])
def test_actual_allocator_future_prices_cannot_change_prefix(daily):
    base, base_trace, start, cutoff = _allocator_prefix_case(daily=daily)
    changed, changed_trace, _, _ = _allocator_prefix_case(future_changed=True, daily=daily)
    assert base[0][:cutoff - start] == changed[0][:cutoff - start]
    before = [(day, weights) for day, weights in base[2] if day <= cutoff]
    after = [(day, weights) for day, weights in changed[2] if day <= cutoff]
    assert before[-1][0] == cutoff and before == after
    assert [row for row in base_trace if row["day"] <= cutoff] == [
        row for row in changed_trace if row["day"] <= cutoff]


@pytest.mark.parametrize("daily", [False, True], ids=["weekly", "daily_fixture"])
def test_actual_allocator_next_day_canary_is_detected_at_cutoff(daily):
    base, _, start, cutoff = _allocator_prefix_case(leaky=True, daily=daily)
    changed, _, _, _ = _allocator_prefix_case(future_changed=True, leaky=True, daily=daily)
    before = [(day, weights) for day, weights in base[2] if day <= cutoff]
    after = [(day, weights) for day, weights in changed[2] if day <= cutoff]
    assert before[:-1] == after[:-1]
    assert before[-1][0] == after[-1][0] == cutoff
    assert before[-1][1] != after[-1][1]
    # Its cutoff decision executes tomorrow; NAV alone would miss this leak.
    assert base[0][:cutoff - start] == changed[0][:cutoff - start]
