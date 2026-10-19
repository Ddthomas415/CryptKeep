"""ED-001 WP4 item 1: contract tests for the reviewed research harness, on SYNTHETIC data only.

Contracts (each has a hand-calculated case and a deliberately corrupted variant that must be detected):
  A.  Look-ahead: scrambling prices after a cutoff decision day cannot change (i) NAV on or before that day or
      (ii) any target decision made on or before that day, INCLUDING the decision made at the cutoff close
      (decide at close i, execute at open i+1; scripts/research/rerun_frozen_stress.py run()). Decisions are
      compared by their decision-day index, because a decision at close i only reaches NAV from day i+1.
  B1. Fixed fills: with the executed quantities and execution prices held identical, a higher fee gives lower
      cash and lower NAV. Fees are applied by a small test-local settlement ledger (_settle), which is first
      anchored to the harness: at the reference fee it must reproduce rebalance()'s cash exactly.
  B2. Dynamic sizing (separate, weaker check): with target weights and prices held fixed, rebalance() re-sizes
      quantities after costs; NAV must still fall as the fee rises. This is NOT the fixed-fill contract.
  C.  Cash floor and affordability: every rebalance() result is reconciled to an explicit ledger of cash credits
      (sells: qty * price * (1 - slip) * (1 - fee)) and debits (buys: qty * price * (1 + slip) * (1 + fee)),
      settled sells-first. Cash must never go negative at any ledger step, the ledger's final cash must equal
      rebalance()'s cash, and post-trade value marked at execution prices must not exceed pre-trade value.
      Convention: rebalance() is a simultaneous rebalance; affordability is defined with sells settling before buys.
No market data is read, no production or research code is modified, and no strategy result is computed on
market data.
"""
import datetime as dt
import json
import math
import random

import pytest

from scripts.research.corrected_research_math import rebalance
from scripts.research.rerun_frozen_stress import load_frozen, run


# ---------- synthetic data ----------
def _write_synthetic(dir_, seed=11, scramble_after=None, scramble_seed=99):
    """Daily BTC/ETH rows [ts, open, high, low, close, volume] for 2016-05-01..2026-10-10, seeded random walk.
    Rows with ts > scramble_after get independent random prices (the 'future' is replaced)."""
    rng, srng = random.Random(seed), random.Random(scramble_seed)
    (dir_ / "maj").mkdir(parents=True, exist_ok=True)
    start, end = dt.date(2016, 5, 1), dt.date(2026, 10, 10)
    for name, p0 in (("BTC-USD", 450.0), ("ETH-USD", 10.0)):
        rows, p, d = [], p0, start
        while d <= end:
            ts = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())
            o = p; c = p * math.exp(rng.gauss(0.0005, 0.04)); p = c
            if scramble_after is not None and ts > scramble_after:
                o, c = srng.uniform(1, 1e5), srng.uniform(1, 1e5)
            rows.append([ts, o, max(o, c), min(o, c), c, 1.0])
            d += dt.timedelta(days=1)
        (dir_ / "maj" / f"{name}_d1.json").write_text(json.dumps(rows))
    return dir_


# ---------- explicit settlement ledger (test-local; not production code) ----------
def _settle(cash, units, fills, fee, slip, sell_fee=None):
    """Apply fills [(asset, signed_qty, exec_price)] sells-first. Returns (cash, units, min_cash_seen).
    sell_fee lets a corrupted variant charge a different fee on sells (default: same fee)."""
    sf = fee if sell_fee is None else sell_fee
    units, min_cash = dict(units), cash
    for asset, q, px in sorted(fills, key=lambda f: f[1] >= 0):          # sells (q < 0) first
        if q < 0:
            cash += -q * px * (1 - slip) * (1 - sf)
        else:
            cash -= q * px * (1 + slip) * (1 + fee)
        units[asset] = units.get(asset, 0.0) + q
        min_cash = min(min_cash, cash)
    return cash, units, min_cash


def _fills(units_before, units_after, prices):
    return [(a, units_after.get(a, 0.0) - units_before.get(a, 0.0), prices[a])
            for a in prices if units_after.get(a, 0.0) != units_before.get(a, 0.0)]


# ---------- A. look-ahead ----------
DECISION_WEEKDAY = 6          # run()'s default wd: decisions at lo and on days k (lo < k < hi) with WD[k] == 6


def _curve_until(ns, lo, hi, cutoff_index):
    curve, _ = run(ns, "rule", lo, hi, fee=0.005, slip=0.0005)
    return curve[: cutoff_index - lo + 1]


def _recording(ns, log):
    # Wrap the (possibly corrupted) target so every call is logged as (decision_day_index, returned weights).
    inner = ns["target"]
    def t(kind, i, L, V, assets, expo=None):
        w = inner(kind, i, L, V, assets, expo)
        log.append((i, None if w is None else dict(w)))
        return w
    return t


def _lookahead_compare(tmp_path, wrap_target=None):
    """Returns (nav_diff, base_decisions, pert_decisions, cut). Decisions are lists of (day_index, weights) with
    day_index <= cut. cut is the first decision day at or after lo + 400, so a decision is made AT the cutoff close."""
    base = load_frozen(_write_synthetic(tmp_path / "base"))
    lo, hi = base["PER"]["B"]
    cut = lo + 400
    while base["WD"][cut] != DECISION_WEEKDAY:
        cut += 1
    assert lo < cut < hi
    cutoff_ts = base["days"][cut]
    pert = load_frozen(_write_synthetic(tmp_path / "pert", scramble_after=cutoff_ts))
    assert pert["WD"][cut] == DECISION_WEEKDAY and pert["days"][cut] == cutoff_ts
    logs = {"base": [], "pert": []}
    for name, ns in (("base", base), ("pert", pert)):
        if wrap_target:
            ns["target"] = wrap_target(ns)
        ns["target"] = _recording(ns, logs[name])
    a, b = _curve_until(base, lo, hi, cut), _curve_until(pert, lo, hi, cut)
    assert len(a) == len(b) == cut - lo + 1
    nav_diff = max(abs(x - y) for x, y in zip(a, b))
    dec = {k: [(i, w) for i, w in v if i <= cut] for k, v in logs.items()}
    return nav_diff, dec["base"], dec["pert"], cut


def test_A_future_prices_cannot_change_past_nav(tmp_path):
    # Expectation: NAV through the cutoff day depends only on prices up to that day, so the difference must be
    # exactly 0.0 (identical float operations on identical inputs).
    nav_diff, _, _, _ = _lookahead_compare(tmp_path)
    assert nav_diff == 0.0


def test_A_future_prices_cannot_change_decisions_through_cutoff(tmp_path):
    # Expectation: every decision made at a close on or before the cutoff -- including the cutoff close itself,
    # whose trade executes after the NAV window -- is identical, aligned by decision-day index.
    _, base_dec, pert_dec, cut = _lookahead_compare(tmp_path)
    assert [i for i, _ in base_dec] == [i for i, _ in pert_dec]
    assert base_dec[-1][0] == cut                       # the cutoff decision is part of the comparison
    assert base_dec == pert_dec


def test_A_corrupted_leaky_target_is_detected(tmp_path):
    # Corruption: a target whose BTC weight depends strictly monotonically on the NEXT day's close:
    #   w_BTC = 0.5 * P[i+1] / (P[i+1] + P[i]),  w_ETH = 0.
    # Decisions before the cutoff peek only at unscrambled closes, so they match; the decision AT the cutoff peeks
    # at the scrambled close of cut + 1, so it must differ. NAV through the cutoff cannot show this leak (its
    # trade executes at open cut + 1), which is why decisions are compared by index.
    def leaky(ns):
        P, real = ns["P"], ns["target"]
        def t(kind, i, L, V, assets, expo=None):
            if kind == "rule" and i + 1 < len(P["BTC"]):
                nxt, now = P["BTC"][i + 1], P["BTC"][i]
                return {"BTC": 0.5 * nxt / (nxt + now), "ETH": 0.0}
            return real(kind, i, L, V, assets, expo)
        return t
    nav_diff, base_dec, pert_dec, cut = _lookahead_compare(tmp_path, wrap_target=leaky)
    assert [i for i, _ in base_dec] == [i for i, _ in pert_dec]
    assert base_dec[-1][0] == pert_dec[-1][0] == cut
    assert base_dec[:-1] == pert_dec[:-1]               # earlier decisions saw only unscrambled closes
    assert base_dec[-1][1] != pert_dec[-1][1]           # specific failure: the cutoff decision differs
    assert nav_diff == 0.0                              # NAV alone misses this leak (the original off-by-one)


# ---------- B1. fees with fills held fixed ----------
FEES = (0.0, 0.001, 0.005, 0.01, 0.02)


def test_B1_hand_calculated_fixed_fills():
    # Fills: buy 5 BTC at 100, then sell 2 BTC at 120; slip 0; mark 3 BTC at 120.
    #   fee 0%: cash 1000 - 500 + 240.0 = 740.0  -> NAV 740.0 + 360 = 1100.0
    #   fee 1%: cash 1000 - 505 + 237.6 = 732.6  -> NAV 1092.6
    #   fee 2%: cash 1000 - 510 + 235.2 = 725.2  -> NAV 1085.2
    expected = {0.0: 1100.0, 0.01: 1092.6, 0.02: 1085.2}
    for fee, nav in expected.items():
        cash, units, _ = _settle(1000.0, {}, [("BTC", 5.0, 100.0)], fee, 0.0)
        cash, units, _ = _settle(cash, units, [("BTC", -2.0, 120.0)], fee, 0.0)
        assert units["BTC"] == 3.0
        assert cash + units["BTC"] * 120.0 == pytest.approx(nav, rel=1e-12)


def _reference_path(fee_ref=0.005, slip=0.0005):
    # Fixed decisions and prices; rebalance() at the reference fee produces the fills that are then held fixed.
    opens = [100.0, 120.0, 90.0, 130.0]
    weights = [{"BTC": 0.8}, {"BTC": 0.2}, {"BTC": 0.9}, {}]
    cash, units, steps = 1000.0, {}, []
    for o, w in zip(opens, weights):
        prices = {"BTC": o}
        c2, u2 = rebalance(cash, units, prices, w, fee_ref, slip)
        steps.append((cash, units, _fills(units, u2, prices), c2, u2))
        cash, units = c2, u2
    return steps


def test_B1_ledger_reproduces_harness_at_reference_fee():
    # Anchor: the test-local ledger must reproduce rebalance()'s cash at every step of the reference path,
    # so B1's fee comparison uses the harness's own cost convention.
    for cash, units, fills, harness_cash, _ in _reference_path():
        ledger_cash, _, _ = _settle(cash, units, fills, 0.005, 0.0005)
        assert ledger_cash == pytest.approx(harness_cash, rel=1e-9, abs=1e-9)


def test_B1_corrupted_ledger_without_sell_fees_is_detected():
    # Corruption: a ledger that charges no fee on sells no longer reproduces the harness (path has sells).
    mismatches = 0
    for cash, units, fills, harness_cash, _ in _reference_path():
        ledger_cash, _, _ = _settle(cash, units, fills, 0.005, 0.0005, sell_fee=0.0)
        mismatches += abs(ledger_cash - harness_cash) > 1e-6
    assert mismatches > 0


def _replay_states(fee, reset_each_step=False):
    # Chained replay of the saved fills from the path's true starting state (cash 1000, no holdings).
    # Each step starts from the state the previous step left. reset_each_step=True is the corrupted variant.
    states, cash, units = [], 1000.0, {}
    for _, _, fills, _, _ in _reference_path():
        if reset_each_step:
            cash, units = 1000.0, {}
        cash, units, _ = _settle(cash, units, fills, fee, 0.0005)
        states.append((cash, units))
    return states


def test_B1_chained_replay_reproduces_harness_path_at_reference_fee():
    # At the reference fee, replaying the saved fills step by step from (1000, {}) must reproduce the harness's
    # cash AND holdings after every step, so each fill is applied to the state it was generated from.
    for (cash, units), (_, _, _, h_cash, h_units) in zip(_replay_states(0.005), _reference_path()):
        assert cash == pytest.approx(h_cash, rel=1e-9, abs=1e-9)
        assert units.get("BTC", 0.0) == pytest.approx(h_units.get("BTC", 0.0), rel=1e-12, abs=1e-12)


def test_B1_holdings_path_is_identical_across_fees():
    # Fixed fills: holdings after every step are the same at every fee; only cash may differ.
    ref = [u.get("BTC", 0.0) for _, u in _replay_states(0.005)]
    for fee in FEES:
        assert [u.get("BTC", 0.0) for _, u in _replay_states(fee)] == ref


def test_B1_corrupted_replay_reset_each_step_is_detected():
    # Corruption: replaying each step's fills against the ORIGINAL state (1000, {}) instead of the prior step's
    # state. Step 2 of the reference path is a sell (BTC weight 0.8 -> 0.2 at 120), so applying it to an empty
    # account must leave NEGATIVE BTC holdings; the replayed path must also disagree with the harness path.
    path = _reference_path()
    step2_fills = path[1][2]
    assert len(step2_fills) == 1 and step2_fills[0][0] == "BTC" and step2_fills[0][1] < 0   # premise: a sell
    broken = _replay_states(0.005, reset_each_step=True)
    assert broken[1][1]["BTC"] < 0.0                                                           # specific failure
    assert any(abs(cash - h[3]) > 1e-6 or abs(units.get("BTC", 0.0) - h[4].get("BTC", 0.0)) > 1e-9
               for (cash, units), h in zip(broken, path))                                     # path mismatch


def _fixed_fill_navs(settle=_settle):
    steps = _reference_path()
    navs = []
    for fee in FEES:
        cash, units = 1000.0, {}
        for _, _, fills, _, _ in steps:                    # identical quantities and execution prices
            cash, units, _ = settle(cash, units, fills, fee, 0.0005)
        navs.append(cash + units.get("BTC", 0.0) * 130.0)
    return navs


def test_B1_higher_fees_lower_nav_with_fills_fixed():
    navs = _fixed_fill_navs()
    assert all(a > b for a, b in zip(navs, navs[1:])), navs


def test_B1_corrupted_fee_ignored_is_detected():
    # Corruption: a ledger that ignores the fee -> every NAV is identical, so strict decrease must fail.
    navs = _fixed_fill_navs(settle=lambda c, u, f, fee, slip: _settle(c, u, f, 0.0, slip))
    assert not all(a > b for a, b in zip(navs, navs[1:]))


# ---------- B2. dynamic sizing (separate, weaker check) ----------
def _hand_case(fee, slip=0.0):
    # Cash 1000, rebalance to 50% BTC at open 100 (ETH price 10, weight 0), then mark at close 110.
    cash, units = rebalance(1000.0, {}, {"BTC": 100.0, "ETH": 10.0}, {"BTC": 0.5}, fee, slip)
    return cash + units["BTC"] * 110.0 + units.get("ETH", 0.0) * 10.0, cash, units


def test_B2_hand_calculated_dynamic_sizing():
    # fee 1%, slip 0: post-cost equity E solves E + 0.01 * 0.5 * E = 1000 -> E = 1000 / 1.005 = 995.0248756...
    # cash = 0.5 E = 497.5124378; BTC units = 0.5 E / 100 = 4.975124378; NAV at 110 = 497.5124378 + 547.2636816.
    nav, cash, units = _hand_case(0.01)
    assert cash == pytest.approx(500 / 1.005, rel=1e-12)
    assert units["BTC"] == pytest.approx(5 / 1.005, rel=1e-12)
    assert nav == pytest.approx(1044.7761194, rel=1e-9)
    assert _hand_case(0.0)[0] == pytest.approx(1050.0, rel=1e-12)   # no fee: 500 cash + 5 BTC * 110


def _dynamic_navs(rb=rebalance):
    opens = [100.0, 120.0, 90.0, 130.0]
    weights = [{"BTC": 0.8}, {"BTC": 0.2}, {"BTC": 0.9}, {}]
    navs = []
    for fee in FEES:
        cash, units = 1000.0, {}
        for o, w in zip(opens, weights):
            cash, units = rb(cash, units, {"BTC": o}, w, fee, 0.0005)
        navs.append(cash + units.get("BTC", 0.0) * 130.0)
    return navs


def test_B2_dynamic_sizing_higher_fees_lower_nav():
    navs = _dynamic_navs()
    assert all(a > b for a, b in zip(navs, navs[1:])), navs


def test_B2_corrupted_fee_ignored_is_detected():
    broken = lambda c, u, p, w, fee, slip: rebalance(c, u, p, w, 0.0, slip)
    navs = _dynamic_navs(rb=broken)
    assert not all(a > b for a, b in zip(navs, navs[1:]))


# ---------- C. cash floor and affordability ----------
def test_C_hand_calculated_full_allocation():
    # 100% into BTC at 100 with fee 1%, slip 0: E = 1000 / 1.01; cash = 0 (not negative); units = 10 / 1.01.
    cash, units = rebalance(1000.0, {}, {"BTC": 100.0}, {"BTC": 1.0}, 0.01, 0.0)
    assert cash == 0.0
    assert units["BTC"] == pytest.approx(10 / 1.01, rel=1e-12)


def _sell_btc_buy_eth(rb):
    # Start: cash 100, 5 BTC at 100, 0 ETH at 10; target {ETH: 0.5}; fee 1%, slip 0.
    return rb(100.0, {"BTC": 5.0, "ETH": 0.0}, {"BTC": 100.0, "ETH": 10.0}, {"ETH": 0.5}, 0.01, 0.0)


def test_C_hand_calculated_sell_then_buy_ledger():
    # before = 600. Costs: sell 500 * 1% = 5; buy 0.5 E * 1%. E + 5 + 0.005 E = 600 -> E = 595 / 1.005 = 592.0398010.
    #   sell credit  = 5 * 100 * 0.99            = 495.0      cash after sell = 100 + 495 = 595.0
    #   ETH notional = 0.5 E                     = 296.0199005; units = 29.60199005
    #   buy debit    = 296.0199005 * 1.01        = 298.9800995 (<= 595.0 available: affordable)
    #   final cash   = 595.0 - 298.9800995       = 296.0199005 (= 0.5 E, >= 0)
    cash, units = _sell_btc_buy_eth(rebalance)
    E = 595 / 1.005
    assert units["BTC"] == 0.0
    assert units["ETH"] == pytest.approx(0.5 * E / 10, rel=1e-12)
    assert cash == pytest.approx(0.5 * E, rel=1e-12)
    fills = _fills({"BTC": 5.0, "ETH": 0.0}, units, {"BTC": 100.0, "ETH": 10.0})
    ledger_cash, _, min_cash = _settle(100.0, {"BTC": 5.0, "ETH": 0.0}, fills, 0.01, 0.0)
    assert min_cash >= 0.0
    assert ledger_cash == pytest.approx(cash, rel=1e-12)
    assert ledger_cash == pytest.approx(100 + 495 - 0.5 * E * 1.01, rel=1e-12)


def _rebalance_without_sell_costs(cash, units, prices, weights, fee, slip):
    # Corruption: same bisection as the harness, but sells cost nothing -> cash overstated vs the ledger.
    before = cash + sum(units.get(a, 0) * prices[a] for a in prices)
    def cost(e):
        return sum(max(0.0, weights.get(a, 0) * e - units.get(a, 0) * p) * ((1 + slip) * (1 + fee) - 1)
                   for a, p in prices.items())
    lo, hi = 0.0, before
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if mid + cost(mid) > before else (mid, hi)
    e = (lo + hi) / 2
    return e * max(0.0, 1 - sum(weights.values())), {a: weights.get(a, 0) * e / p for a, p in prices.items()}


def test_C_corrupted_sell_costs_dropped_is_detected():
    # Corrupted E = 600 / 1.005 = 597.0149; claimed cash 298.5075 vs ledger 595 - 298.5075 * 1.01 = 293.5075.
    cash, units = _sell_btc_buy_eth(_rebalance_without_sell_costs)
    fills = _fills({"BTC": 5.0, "ETH": 0.0}, units, {"BTC": 100.0, "ETH": 10.0})
    ledger_cash, _, _ = _settle(100.0, {"BTC": 5.0, "ETH": 0.0}, fills, 0.01, 0.0)
    assert abs(ledger_cash - cash) > 1.0


def _cash_violations(rb, n=2000, seed=3):
    rng, bad = random.Random(seed), 0
    for _ in range(n):
        prices = {"BTC": rng.uniform(1, 1e5), "ETH": rng.uniform(1, 1e4)}
        units = {a: rng.choice([0.0, rng.uniform(0, 3)]) for a in prices}
        cash = rng.choice([0.0, rng.uniform(0, 5000)])
        if cash + sum(units[a] * prices[a] for a in prices) <= 0:
            continue
        w1 = rng.choice([0.0, rng.uniform(0, 1)]); w2 = rng.uniform(0, 1 - w1)
        fee, slip = rng.uniform(0, 0.02), rng.uniform(0, 0.005)
        before = cash + sum(units[a] * prices[a] for a in prices)
        c2, u2 = rb(cash, units, prices, {"BTC": w1, "ETH": w2}, fee, slip)
        after = c2 + sum(u2[a] * prices[a] for a in prices)
        ledger_cash, _, min_cash = _settle(cash, units, _fills(units, u2, prices), fee, slip)
        tol = 1e-9 * max(1.0, before)
        if (c2 < -1e-9 or min_cash < -tol or abs(ledger_cash - c2) > tol
                or after > before * (1 + 1e-12)):
            bad += 1
    return bad


def test_C_cash_never_negative_and_every_trade_affordable():
    assert _cash_violations(rebalance) == 0


def test_C_corrupted_pre_cost_sizing_is_detected():
    # Corruption: size every target on PRE-cost value and pay additive costs from cash -> negative cash near full
    # allocation and cash that disagrees with the ledger whenever fee and slip are both nonzero.
    def naive(cash, units, prices, weights, fee, slip):
        before = cash + sum(units.get(a, 0) * prices[a] for a in prices)
        new = {a: weights.get(a, 0) * before / prices[a] for a in prices}
        costs = sum(abs(new[a] - units.get(a, 0)) * prices[a] * (fee + slip) for a in prices)
        return before - sum(new[a] * prices[a] for a in prices) - costs, new
    assert _cash_violations(naive) > 0
