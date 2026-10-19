import datetime as dt

import numpy as np
import pytest

from scripts.research.rerun_frozen_hybrid import run

# 2023-12-31 is a Sunday: START decision at its close, first execution at Monday's open.
D0 = int(dt.datetime(2023, 12, 31, tzinfo=dt.timezone.utc).timestamp())


def make_ns(days=10, target=None):
    C = np.full((days, 2), 100.0); O = np.full((days, 2), 100.0)
    return {"C": C, "O": O, "syms": ["AAAUSDT", "BTCUSDT"], "D0": D0, "ND": days, "START": 0, "BTC": 1,
            "weights": lambda name, L, i: dict(target if target is not None else {0: 0.5})}


def test_decision_at_close_executes_at_next_open():
    ns = make_ns(); ns["O"][1, 0] = 125.0  # Monday open differs from Sunday close
    meta, curve = run(ns, "equal_weight_top20", 0, 0.0, "strict")
    # shared rebalance(): post-cost equity solves after * (1 + 0.5 * 0.0005) = 1000; half bought at the 125 open
    after = 1000 / (1 + 0.5 * 0.0005)
    assert curve[1][1] == pytest.approx(after * 0.5 + after * 0.5 / 125 * 100, rel=1e-6)


def test_missing_held_close_stops_strict_run():
    ns = make_ns(); ns["C"][3, 0] = np.nan
    meta, _ = run(ns, "equal_weight_top20", 0, 0.0, "strict")
    assert meta["status"] == "INCOMPLETE" and "no close" in meta["stopped_at"]


def test_outage_leaves_nav_unknown_instead_of_zero_return():
    ns = make_ns(); ns["C"][3, 0] = np.nan
    meta, curve = run(ns, "equal_weight_top20", 0, 0.0, "outage")
    assert meta["status"] == "COMPLETE" and dict(curve)[3] is None


def test_target_without_open_stays_in_cash():
    ns = make_ns(); ns["O"][1, 0] = np.nan
    meta, curve = run(ns, "equal_weight_top20", 0, 0.0, "strict")
    assert meta["targets_skipped_no_open"] == 1 and curve[1][1] == pytest.approx(1000.0)


def test_btc_hold_buys_once_at_first_open():
    ns = make_ns(); ns["O"][1, 1] = 110.0; ns["C"][:, 1] = 110.0
    meta, curve = run(ns, "btc_hold", 0, 0.0, "strict")
    assert curve[-1][1] == pytest.approx(1000 / 1.0005, rel=1e-6)


def test_identity_break_after_gap_stops_outage_run():
    ns = make_ns(); ns["C"][3:5, 0] = np.nan; ns["O"][3:5, 0] = np.nan
    ns["C"][5:, 0] = 100.0 * 20000; ns["O"][5:, 0] = 100.0 * 20000   # relisted as a different asset
    meta, _ = run(ns, "equal_weight_top20", 0, 0.0, "outage")
    assert meta["status"] == "INCOMPLETE" and "identity break" in meta["stopped_at"]


def test_ordinary_gap_without_identity_break_continues_in_outage():
    ns = make_ns(); ns["C"][3:5, 0] = np.nan; ns["O"][3:5, 0] = np.nan; ns["C"][5:, 0] = 130.0
    meta, _ = run(ns, "equal_weight_top20", 0, 0.0, "outage")
    assert meta["status"] == "COMPLETE"
