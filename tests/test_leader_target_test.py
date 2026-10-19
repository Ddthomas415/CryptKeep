from scripts.research.leader_target_test import DAY, simulate


def rows(prices):
    return {i*DAY: {'open': p, 'close': p} for i, p in enumerate(prices)}


def test_target_above_entry_not_first_green():
    r = rows([100, 80, 70, 71, 74, 75, 75])
    e = simulate(r, 0, 7*DAY, .1, .05, 7, .005, .0025)
    assert e['exit_time'] == 5*DAY
    assert e['net_pnl_usd'] > 0
    del r[6*DAY]
    assert simulate(r, 0, 7*DAY, .1, .05, 7, .005, .0025) == e


def test_timeout_loss_and_unfinished_are_retained():
    r = rows([100, 80, 70, 60, 50, 40, 40])
    e = simulate(r, 0, 7*DAY, .1, .05, 2, .005, .0025)
    assert e['status'] == 'TIMEOUT_EXIT'
    assert e['net_pnl_usd'] < 0
    assert simulate(r, 0, 3*DAY, .1, .05, 7, .005, .0025)['status'] == 'OPEN_AT_SEGMENT_END'


def test_fee_and_spread_budget():
    e = simulate(rows([100, 80, 70, 70, 70]), 0, 5*DAY, .1, .05, 1, .005, .0025)
    assert -16 < e['net_pnl_usd'] < -14
