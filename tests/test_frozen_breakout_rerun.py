import pytest

from scripts.research.rerun_frozen_breakout import calendar_block_mean, observed_trade


def test_exit_is_open_after_full_hold_not_forward_filled_close():
    opens = [100.0] * 75
    opens[1], opens[73] = 110, 80
    value, reason = observed_trade(opens, [True] * 75, 0)
    assert reason is None
    assert value == pytest.approx(80 / 110 * .999 * .995 / (1.001 * 1.005) - 1)


def test_missing_interior_candle_has_no_trade_return():
    present = [True] * 75
    present[40] = False
    assert observed_trade([100.0] * 75, present, 0) == (None, "missing_candle")


def test_immature_is_not_liquidated_at_last_close():
    assert observed_trade([100.0] * 73, [True] * 73, 0) == (None, "immature")


def test_calendar_blocks_keep_same_day_cross_coin_dependence():
    result = calendar_block_mean([(d, x) for d in range(60) for x in (.1, -.1)], 60)
    assert result["mean"] == result["p025"] == result["p975"] == 0


def test_empty_samples_never_receive_an_interval():
    result = calendar_block_mean([(59, .1)], 60)
    assert result["status"] == "INCOMPLETE"
    assert result["undefined_replicates"] > 0
    assert result["p025"] is result["p975"] is None
