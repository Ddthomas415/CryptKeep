import pytest

from scripts.research.rerun_frozen_stress import run


def make_ns(n=6):
    P = {"BTC": [100.0] * n, "ETH": [10.0] * n}
    O = {"BTC": [100.0] * n, "ETH": [10.0] * n}
    target = lambda kind, i, L, V, assets, expo: {"BTC": 1.0} if kind == "hold_btc" else {"BTC": 0.5}
    return {"P": P, "OPEN": O, "WD": [6, 0, 1, 2, 3, 4], "target": target}


def test_initial_decision_trades_at_next_open_not_deciding_close():
    ns = make_ns(); ns["OPEN"]["BTC"][1] = 125.0
    curve, _ = run(ns, "hold_btc", 0, 5, fee=0.0, slip=0.0)
    assert curve[1] == pytest.approx(1000 / 125 * 100)


def test_rebalance_on_decision_weekday_executes_next_day():
    ns = make_ns(); ns["WD"] = [0, 6, 0, 1, 2, 3]
    calls = []
    base = ns["target"]
    ns["target"] = lambda kind, i, *a: calls.append(i) or base(kind, i, *a)
    run(ns, "rule", 0, 5, fee=0.0, slip=0.0)
    assert calls == [0, 1]  # initial decision at lo, then the Sunday close (index 1)
