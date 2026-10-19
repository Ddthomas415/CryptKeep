import pytest

from scripts.research.run_daily_trend_recent_check import window


def test_fixed_windows_are_adjacent_and_include_leap_day():
    windows = [window(y) for y in (2024, 2025, 2026)]
    assert [w[2] for w in windows] == [366, 365, 365]
    for start, end, days in windows:
        assert end-start == (days+200)*86400
    for previous, following in zip(windows, windows[1:]):
        assert previous[1] == following[0]+200*86400


def test_unknown_year_rejected():
    with pytest.raises(ValueError):
        window(2027)
