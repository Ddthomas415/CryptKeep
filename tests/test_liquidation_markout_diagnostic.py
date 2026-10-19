import pytest

from scripts.research.liquidation_markout_diagnostic import MINUTE, outcome, spaced, summarize


def candles():
    return {i * MINUTE: [i * MINUTE, '100', '120', '90', str(100 + i), '1', '1', '1', '1']
            for i in range(1, 17)}


def test_fixed_horizon_correct_open_close_and_cost_reference():
    result = outcome(candles(), MINUTE, 5, 20 * MINUTE, .005, .0025, 1000)
    assert result['reference_open'] == 100
    assert result['forward_close'] == 105
    assert result['gross_move_quote_reference'] == pytest.approx(50)
    assert result['modeled_cost_adjusted_reference'] == pytest.approx(1000 * (105 * .9975 * .995 / (100 * 1.0025 * 1.005) - 1))


def test_gap_or_unconfirmed_middle_bar_is_unknown_not_skipped():
    rows = candles()
    del rows[3 * MINUTE]
    assert outcome(rows, MINUTE, 5, 20 * MINUTE, 0, 0, 1000)['status'] == 'MISSING_OR_UNCONFIRMED_PRICE'
    rows = candles()
    rows[3 * MINUTE][-1] = '0'
    assert outcome(rows, MINUTE, 5, 20 * MINUTE, 0, 0, 1000)['status'] == 'MISSING_OR_UNCONFIRMED_PRICE'


def test_immature_horizon_is_not_zero_or_failed_recovery():
    result = outcome({}, MINUTE, 15, 5 * MINUTE, 0, 0, 1000)
    assert result['status'] == 'IMMATURE'
    summary = summarize([result])
    assert summary['price_declines'] == 0
    assert summary['mean_gross_return'] is None


def test_small_rebound_can_be_negative_after_modeled_costs():
    rows = candles()
    rows[MINUTE][4] = '100.5'
    result = outcome(rows, MINUTE, 1, 20 * MINUTE, .005, .0025, 1000)
    assert result['gross_return'] > 0
    assert result['modeled_cost_adjusted_reference'] < 0


def test_all_declines_are_counted():
    rows = candles()
    rows[MINUTE][4] = '90'
    result = summarize([outcome(rows, MINUTE, 1, 20 * MINUTE, 0, 0, 1000)])
    assert result['price_declines'] == 1
    assert result['mean_gross_return'] == pytest.approx(-.1)
    assert result['mathematical_break_even_fee_per_side_without_adverse'] is None


def test_positive_average_reports_fee_budget_not_verified_profit():
    observation = outcome(candles(), MINUTE, 5, 20 * MINUTE, .005, .0025, 1000)
    result = summarize([observation])
    fee = result['mathematical_break_even_fee_per_side_without_adverse']
    assert fee == pytest.approx(.05 / 2.05)
    assert 1.05 * (1 - fee) / (1 + fee) - 1 == pytest.approx(0)


def test_nonoverlap_selects_earliest_not_best_future_outcome():
    assert spaced([15 * MINUTE, MINUTE, 2 * MINUTE, 16 * MINUTE, 17 * MINUTE], 15 * MINUTE) == [MINUTE, 16 * MINUTE]


def test_future_bars_after_endpoint_cannot_change_markout():
    rows = candles()
    first = outcome(rows, MINUTE, 5, 20 * MINUTE, 0, 0, 1000)
    rows[6 * MINUTE][4] = '1000000'
    assert outcome(rows, MINUTE, 5, 20 * MINUTE, 0, 0, 1000) == first
