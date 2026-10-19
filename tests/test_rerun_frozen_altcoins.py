import numpy as np
import pytest

from scripts.research.rerun_frozen_altcoins import event_portfolio, weight_portfolio


def make_ns(days=10):
    C = np.full((days, 2), 100.0)
    return {"C": C, "syms": ["AAAUSDT", "BTCUSDT"], "D0": 0, "ND": days, "NS": 2}


def run(ns, O, L, sig_day=1, T=None, H=100, mode="strict", last=None):
    last = np.array([ns["ND"] - 1, ns["ND"] - 1]) if last is None else last
    sig = lambda i: [0] if i == sig_day else []
    return event_portfolio(ns, O, L, last, sig, lambda i, j: 1.0, T, H, 0.0, 0.0, 0, ns["ND"] - 1, mode)


def test_entry_fills_at_next_open_not_signal_close():
    ns = make_ns(); O = ns["C"].copy(); L = ns["C"].copy()
    O[2, 0] = 125.0  # signal close 100 on day 1, next open 125
    res, curve = run(ns, O, L, H=3)
    assert res["trades"] == 1
    # bought 100 USD at 125, sold at 100 (time exit at a later open)
    assert res["mean_trade_pct"] == pytest.approx((100 / 125 - 1) * 100, abs=0.01)


def test_close_below_trailing_stop_exits_at_next_open_not_stop_price():
    ns = make_ns(); O = ns["C"].copy(); L = ns["C"].copy()
    ns["C"][5, 0] = 75.0; L[5, 0] = 74.0  # close breaks the 80 stop (T=0.2 of peak close 100)
    O[6, 0] = 70.0                       # next open gaps lower: fill there, not at 80
    res, _ = run(ns, O, L, T=0.2)
    assert res["stop_exits"] == 1
    assert res["mean_trade_pct"] == pytest.approx(-30.0, abs=0.01)


def test_intraday_touch_with_close_above_stop_does_not_exit():
    ns = make_ns(); O = ns["C"].copy(); L = ns["C"].copy()
    L[5, 0] = 60.0  # low pierces the stop but the frozen rule triggers on closes only
    res, _ = run(ns, O, L, T=0.2)
    assert res["stop_exits"] == 0


def test_missing_candle_of_held_coin_is_incomplete_in_strict_mode():
    ns = make_ns(); O = ns["C"].copy(); L = ns["C"].copy()
    ns["C"][5, 0] = np.nan; O[5, 0] = np.nan; L[5, 0] = np.nan
    res, _ = run(ns, O, L)
    assert res["status"] == "INCOMPLETE" and "missing candle" in res["stopped_at"]


def test_outage_mode_leaves_nav_unknown_not_forward_filled():
    ns = make_ns(); O = ns["C"].copy(); L = ns["C"].copy()
    ns["C"][5, 0] = np.nan; O[5, 0] = np.nan; L[5, 0] = np.nan
    res, curve = run(ns, O, L, mode="outage")
    assert res["status"] == "COMPLETE"
    assert dict(curve)[5] is None


def test_delisted_holding_is_incomplete_not_sold_at_last_close():
    ns = make_ns(); O = ns["C"].copy(); L = ns["C"].copy()
    ns["C"][6:, 0] = np.nan; O[6:, 0] = np.nan; L[6:, 0] = np.nan
    res, _ = run(ns, O, L, mode="outage", last=np.array([5, 9]))
    assert res["status"] == "INCOMPLETE" and "delisted" in res["stopped_at"]


def test_weight_portfolio_delist_scenarios_bound_outcome():
    ns = make_ns(); O = ns["C"].copy()
    ns["C"][6:, 0] = np.nan; O[6:, 0] = np.nan
    last = np.array([5, 9]); target = lambda i: {0: 0.5}
    strict, _ = weight_portfolio(ns, O, last, target, {0}, 0.0, 0.0, 0, 9, "strict")
    keep, c1 = weight_portfolio(ns, O, last, target, {0}, 0.0, 0.0, 0, 9, "delist_last_close")
    zero, c0 = weight_portfolio(ns, O, last, target, {0}, 0.0, 0.0, 0, 9, "delist_zero")
    assert strict["status"] == "INCOMPLETE"
    assert c1[-1][1] == pytest.approx(1000.0) and c0[-1][1] == pytest.approx(500.0)
