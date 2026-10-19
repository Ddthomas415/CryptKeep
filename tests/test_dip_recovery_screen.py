from scripts.research.dip_recovery_screen import screen


def bars(prices):
    return [dict(start=i*3600, open=p, close=p, low=p, high=p)
            for i, p in enumerate(prices)]


def test_target_is_close_trigger_and_exit_next_open():
    data = bars([100, 90, 90, 95, 80, 80, 80])
    result = screen(data, 3600, 1, .03, 3)
    assert result['n'] == 1
    assert result['events'][0]['target_close_reached']
    assert result['events'][0]['exit_time'] == 4*3600
    assert result['events'][0]['gross_return'] < 0


def test_missing_bar_cannot_be_bridged():
    data = bars([100, 90, 90, 95, 95, 95])
    data[3]['start'] += 100
    assert screen(data, 3600, 1, .03, 2)['n'] == 0


def test_no_recovery_timeout_is_included():
    result = screen(bars([100, 90, 90, 80, 70, 60, 60]), 3600, 1, .03, 3)
    assert result['target_hits'] == 0
    assert result['n'] == 1
    assert result['worst_return'] < 0
