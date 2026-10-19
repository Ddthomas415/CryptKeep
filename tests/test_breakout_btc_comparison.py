import pytest

from scripts.research.compare_breakout_btc import benchmark


def test_costs_and_same_open_endpoints():
    result = benchmark([100, 120, 150], [110, 130, 160], [True] * 3, 0, 2, .005)
    assert result["terminal_cash"] == pytest.approx(1000 / (100 * 1.001 * 1.005) * 150 * .999 * .995)
    assert len(result["curve"]) == 2


def test_gap_is_null_not_stale_price():
    result = benchmark([100, 0, 150], [110, 0, 160], [True, False, True], 0, 2, .005)
    assert result["curve"][1]["equity"] is None
    assert result["unpriced_hours"] == 1
    assert not result["drawdown_verified"]


def test_missing_endpoint_cannot_liquidate():
    assert benchmark([100, 0], [100, 0], [True, False], 0, 1, .005)["status"] == "INCOMPLETE"
