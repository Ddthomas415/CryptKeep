from copy import deepcopy

import pytest

from scripts.research.failed_breakout_retest import HOUR, signal, simulate, validate_bar, verify


def bar(open=100, high=110, low=99, close=100, volume=1):
    return dict(open=open, high=high, low=low, close=close, volume=volume)


def fixture():
    series = {i * HOUR: bar() for i in range(35)}
    series[24 * HOUR] = bar(low=95, close=101)
    series[25 * HOUR] = bar(low=98, close=102)
    series[26 * HOUR] = bar(open=103, close=111, high=112)
    series[27 * HOUR] = bar(open=112, close=112, high=113, low=111)
    return {'X': series}


def plan(end=28):
    return dict(start=24 * HOUR, boundary=27 * HOUR, end=end * HOUR,
                initial_cash=1000, lookback=5, retest_hours=3, hold_hours=24,
                fee=.005, adverse_price=.0025)


def test_existing_label_next_bar_retest_next_open_fill_and_costs():
    rows = fixture()
    assert signal(rows['X'], 24 * HOUR, 5)['stop'] == 95
    result = simulate(rows, plan())
    trade = result['trades'][0]
    assert trade['sweep_time'] == 24 * HOUR
    assert trade['decision_time'] == 26 * HOUR
    assert trade['entry_time'] == 26 * HOUR
    assert trade['entry_price'] == 103 * 1.0025
    assert trade['exit_time'] == 27 * HOUR
    assert trade['exit_reason'] == 'RANGE_TARGET_CLOSE'
    assert trade['exit_price'] == 112 * .9975
    assert trade['quantity'] * trade['entry_price'] * 1.005 == pytest.approx(1000)
    assert result['ending_cash'] == pytest.approx(1000 + trade['net_pnl_usd'])


def test_stop_is_close_trigger_next_open_not_stop_price():
    rows = fixture()
    rows['X'][26 * HOUR] = bar(open=103, low=90, close=94)
    rows['X'][27 * HOUR] = bar(open=80, high=85, low=75, close=80)
    result = simulate(rows, plan())
    trade = result['trades'][0]
    assert trade['exit_reason'] == 'STOP_CLOSE'
    assert trade['exit_price'] == 80 * .9975
    assert trade['exit_price'] < trade['stop']


def test_intrabar_target_is_not_a_close_target():
    rows = fixture()
    rows['X'][26 * HOUR] = bar(open=103, high=120, low=100, close=105)
    result = simulate(rows, plan(27))
    assert result['closed_trade_count'] == 0
    assert result['position'] is not None
    assert result['ending_cash'] == 0


def test_reclaim_without_later_retest_does_not_enter():
    rows = fixture()
    rows['X'][25 * HOUR] = bar(low=100, close=102)
    result = simulate(rows, plan())
    assert result['closed_trade_count'] == 0
    assert result['ending_cash'] == 1000


def test_future_candles_cannot_change_first_entry():
    rows = fixture()
    changed = deepcopy(rows)
    changed['X'][29 * HOUR] = bar(open=10000, high=11000, low=9000, close=10000)
    a, b = simulate(rows, plan(30)), simulate(changed, plan(30))
    assert a['trades'][0] == b['trades'][0]


@pytest.mark.parametrize('missing,expected', [(26, 'COMPLETE'), (27, 'INCOMPLETE_EXIT_PRICE_GAP')])
def test_missing_execution_price_never_invented(missing, expected):
    rows = fixture()
    del rows['X'][missing * HOUR]
    result = simulate(rows, plan())
    assert result['status'] == expected
    assert result['closed_trade_count'] == 0
    if missing == 26:
        assert result['ending_cash'] == 1000
    else:
        assert result['ending_nav'] is None
        assert result['position'] is not None


def test_held_gap_is_not_a_valid_endpoint():
    rows = fixture()
    rows['X'][26 * HOUR] = bar(open=103, high=110, close=105)
    del rows['X'][27 * HOUR]
    result = simulate(rows, plan())
    assert result['status'] == 'INCOMPLETE_HELD_PRICE_GAP'
    assert result['ending_nav'] is None


def test_allocator_uses_decision_time_volume_not_future_winner():
    rows = fixture()
    rows['Y'] = deepcopy(rows['X'])
    for i in range(2, 26):
        rows['Y'][i * HOUR]['volume'] = 2
    result = simulate(rows, plan())
    assert result['trades'][0]['symbol'] == 'Y'
    assert result['closed_trade_count'] == 1


def test_cash_is_carried_and_not_reset_at_boundary():
    rows = fixture()
    p = plan(35)
    p['boundary'] = 27 * HOUR
    result = simulate(rows, p)
    assert result['checkpoint']['cash'] == 0
    assert result['checkpoint']['held_symbol'] == 'X'
    assert result['ending_cash'] == pytest.approx(1000 + sum(t['net_pnl_usd'] for t in result['trades']))


def test_timeout_after_fixed_number_of_completed_bars():
    rows = fixture()
    rows['X'][26 * HOUR] = bar(open=103, close=105)
    rows['X'][27 * HOUR] = bar(open=104, close=105)
    p = plan(29)
    p['hold_hours'] = 2
    trade = simulate(rows, p)['trades'][0]
    assert trade['exit_time'] == 28 * HOUR
    assert trade['exit_reason'] == 'TIMEOUT'


def test_invalid_ohlcv_or_frozen_source_refused(tmp_path):
    with pytest.raises(ValueError, match='invalid_ohlcv'):
        validate_bar(0, bar(high=90))
    with pytest.raises(ValueError, match='nonfinite'):
        validate_bar(0, bar(volume=float('nan')))
    (tmp_path / 'source.py').write_text('changed')
    with pytest.raises(ValueError, match='frozen_input_or_source_changed'):
        verify({'root': str(tmp_path), 'inputs': {}, 'sources': {'source.py': 'wrong'}})
