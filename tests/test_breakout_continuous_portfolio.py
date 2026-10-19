import pytest
from scripts.research.rerun_breakout_portfolio import portfolio


def arrays(n=10):
    return [[100.0] * n], [[100.0] * n], [[True] * n]


def test_one_account_pays_both_sides_and_holds_exact_duration():
    o, c, p = arrays()
    r = portfolio(o, c, p, [(0, 0)], 1, 9, slots=1, hold=3)
    assert r["status"] == "COMPLETE_DIAGNOSTIC"
    assert [f["hour"] for f in r["fills"]] == [1, 4]
    assert r["terminal_cash"] == pytest.approx(1000 * .999 * .995 / (1.001 * 1.005))


def test_future_gap_does_not_retroactively_remove_entry():
    o, c, p = arrays()
    p[0][3] = False
    r = portfolio(o, c, p, [(0, 0)], 1, 9, hold=3)
    assert r["status"] == "INCOMPLETE"
    assert r["reason"] == "missing_held_valuation"
    assert r["fills"][0]["side"] == "buy"


def test_missing_exit_open_is_not_filled_at_last_close():
    o, c, p = arrays()
    p[0][4] = False
    r = portfolio(o, c, p, [(0, 0)], 1, 9, hold=3)
    assert r["reason"] == "missing_exit_open"
    assert len(r["fills"]) == 1


def test_terminal_open_liquidation_pays_costs():
    o, c, p = arrays()
    r = portfolio(o, c, p, [(0, 0)], 1, 3, slots=1, hold=72)
    assert r["fills"][-1]["terminal"] is True
    assert r["terminal_cash"] < 1000
def test_outage_has_null_valuation_and_delays_exit():
    o, c, p = arrays()
    p[0][4] = p[0][5] = False
    o[0][6] = 80
    r = portfolio(o, c, p, [(0, 0)], 1, 9, hold=3, outage_policy=True)
    assert r["status"] == "COMPLETE_WITH_UNPRICED_INTERVALS"
    assert r["fills"][-1]["hour"] == 6
    assert r["fills"][-1]["delay_hours"] == 2
    assert r["fills"][-1]["reference_open"] == 80
    assert r["unpriced_hours"] == 2
    assert r["drawdown_verified"] is False
    assert all(v["equity"] is None for v in r["curve"] if v["hour"] in (4, 5))


def test_market_outage_blocks_entry_even_when_flat():
    o, c, p = arrays()
    p[0][1] = False
    r = portfolio(o, c, p, [(0, 0)], 1, 9, outage_policy=True, market_index=0)
    assert not r["fills"]
    assert r["refusals"]["outage_entry_block"] == 1


def test_terminal_outage_does_not_invent_liquidation():
    o, c, p = arrays()
    p[0][3] = False
    r = portfolio(o, c, p, [(0, 0)], 1, 3, outage_policy=True)
    assert r["status"] == "INCOMPLETE"
    assert "terminal_cash" not in r
