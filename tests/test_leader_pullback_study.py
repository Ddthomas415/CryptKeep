from scripts.research.leader_pullback_study import DAY, events_for


def make_rows(prices):
    return {'X': {i*DAY: dict(open=p, close=p, low=p, high=p, volume=1)
                  for i, p in enumerate(prices)}}


def test_green_is_not_necessarily_profitable_and_no_future_admission():
    rows = make_rows([100, 80, 70, 60, 65, 64, 64])
    events = events_for(rows, [(0, 'X', .3)], 7*DAY, .1)
    assert events[0]['entry_price'] == 70
    assert events[0]['status'] == 'GREEN_EXIT'
    assert events[0]['gross_return'] < 0
    del rows['X'][6*DAY]
    changed = events_for(rows, [(0, 'X', .3)], 7*DAY, .1)[0]
    for key in ('entry_time', 'entry_price', 'status', 'exit_time', 'gross_return'):
        assert changed[key] == events[0][key]
    assert changed['above_entry_recovery_status'] == 'RECOVERY_UNKNOWN_GAP'


def test_unfinished_event_is_retained():
    event = events_for(make_rows([100, 80, 70]), [(0, 'X', .2)], 3*DAY, .1)[0]
    assert event['status'] == 'OPEN_AT_END'


def test_gap_is_unknown_not_deleted():
    rows = make_rows([100, 80, 70, 60])
    del rows['X'][DAY]
    assert events_for(rows, [(0, 'X', .2)], 4*DAY, .1)[0]['status'].startswith('UNKNOWN')


def test_timeout_does_not_require_recovery():
    prices = [100, 80] + [70-i for i in range(32)]
    event = events_for(make_rows(prices), [(0, 'X', .2)], len(prices)*DAY, .1)[0]
    assert event['status'] == 'TIMEOUT_EXIT'
    assert event['gross_return'] < 0
    assert event['hours_to_exit'] == 30*24


def test_peak_is_updated_only_as_observed():
    event = events_for(make_rows([100, 120, 108, 109, 110]),
                       [(0, 'X', .2)], 5*DAY, .1)[0]
    assert event['peak_at_trigger'] == 120
    assert event['trigger_time'] == 3*DAY
