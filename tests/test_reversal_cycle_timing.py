from scripts.research.reversal_cycle_timing import summarize


def test_completed_cycle_and_censored_edges():
    data = [(i * 3600, v) for i, v in enumerate([1, -1, -1, 1, 1, -1])]
    result = summarize(data, 3600)
    assert result['red_to_green_to_red']['mean_hours'] == 4
    assert result['green_duration']['mean_hours'] == 2


def test_gap_and_zero_do_not_bridge_cycles():
    result = summarize([(0, 1), (3600, -1), (7200, 0),
                        (10800, 1), (21600, -1)], 3600)
    assert result['red_to_green_to_red']['n'] == 0
