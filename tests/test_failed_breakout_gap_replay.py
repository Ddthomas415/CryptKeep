from copy import deepcopy

import pytest

from scripts.research.failed_breakout_gap_replay import simulate
from tests.test_failed_breakout_retest import bar, fixture, plan, HOUR


def test_ordinary_fills_match_strict_test():
    from scripts.research.failed_breakout_retest import simulate as strict
    rows, p = fixture(), plan()
    a, b = strict(rows, p), simulate(rows, p)
    assert a['ending_nav'] == b['ending_nav']
    assert a['equity'] == b['equity']
    assert a['closed_trade_count'] == b['closed_trade_count']
    for before, after in zip(a['trades'], b['trades']):
        assert before == {k: v for k, v in after.items() if k != 'scheduled_exit_time'}


def test_unvalued_held_hour_retains_position_then_uses_real_bar():
    rows = fixture()
    rows['X'][26 * HOUR] = bar(open=103, close=105)
    del rows['X'][27 * HOUR]
    result = simulate(rows, plan(30))
    assert result['status'] == 'COMPLETE_WITH_UNVALUED_HOURS'
    missing = next(x for x in result['equity'] if x['time'] == 28 * HOUR)
    assert missing['nav'] is None
    assert missing['cash'] == 0
    assert result['counts']['unknown_nav_hours'] == 1
    assert result['position']['symbol'] == 'X'


def test_deferred_sell_never_fills_at_missing_price():
    rows = fixture()
    del rows['X'][27 * HOUR]
    rows['X'][28 * HOUR] = bar(open=80, low=75, high=85, close=80)
    result = simulate(rows, plan(29))
    trade = result['trades'][0]
    assert trade['scheduled_exit_time'] == 27 * HOUR
    assert trade['exit_time'] == 28 * HOUR
    assert trade['exit_price'] == 80 * .9975
    assert result['counts']['deferred_exit_hours'] == 1
    assert result['ending_cash'] == pytest.approx(1000 + trade['net_pnl_usd'])


def test_missing_endpoint_is_not_a_valued_result():
    rows = fixture()
    del rows['X'][27 * HOUR]
    result = simulate(rows, plan())
    assert result['ending_nav'] is None
    assert result['status'] == 'INCOMPLETE_ENDPOINT'
    assert result['pending']['side'] == 'sell'
    assert result['position']['symbol'] == 'X'


def test_unselected_watch_survives_failed_selected_entry():
    rows = fixture()
    rows['Y'] = deepcopy(rows['X'])
    for t in range(24):
        rows['Y'][t * HOUR]['volume'] = 10
    del rows['Y'][26 * HOUR]
    rows['X'][26 * HOUR] = bar(open=102, low=98, close=103)
    rows['X'][27 * HOUR] = bar(open=103, high=112, low=100, close=111)
    rows['X'][28 * HOUR] = bar(open=112, high=113, low=110, close=112)
    result = simulate(rows, plan(29))
    assert result['trades'][0]['symbol'] == 'X'
    assert result['trades'][0]['entry_time'] == 27 * HOUR
    assert result['trades'][0]['sweep_time'] == 24 * HOUR
    assert any(x['kind'] == 'ENTRY_SKIPPED_PRICE_GAP' for x in result['decisions'])


def test_zero_volume_exit_bar_is_not_executable():
    rows = fixture()
    rows['X'][27 * HOUR]['volume'] = 0
    result = simulate(rows, plan(29))
    assert result['trades'][0]['exit_time'] == 28 * HOUR
    assert result['equity'][3]['nav'] is None


def test_unknown_gap_counts_toward_original_wall_clock_timeout():
    rows = fixture()
    rows['X'][26 * HOUR] = bar(open=103, close=105)
    del rows['X'][27 * HOUR]
    rows['X'][28 * HOUR] = bar(open=103, close=105)
    p = plan(30)
    p['hold_hours'] = 2
    trade = simulate(rows, p)['trades'][0]
    assert trade['exit_reason'] == 'TIMEOUT'
    assert trade['exit_time'] == 29 * HOUR
    assert trade['cash_at_entry'] == 1000
