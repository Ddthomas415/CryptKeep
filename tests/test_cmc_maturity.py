from datetime import datetime, timedelta, timezone

import pytest

from scripts.research.cmc_maturity import readiness

START = datetime(2026, 10, 9, tzinfo=timezone.utc)


def test_old_collection_does_not_mature_new_event():
    now = START+timedelta(days=90)
    result = readiness(START, now, now, 30)
    assert result["minimum_collection_age_reached"] is True
    assert result["endpoint_window_closed"] is False
    assert result["scoring_authorized"] is False


def test_window_must_close_including_tolerance():
    edge = START+timedelta(days=7, hours=12)
    assert not readiness(START, START, edge-timedelta(microseconds=1), 7)["endpoint_window_closed"]
    assert readiness(START, START, edge, 7)["endpoint_window_closed"]


def test_invalid_order_and_naive_time():
    with pytest.raises(ValueError):
        readiness(START, START+timedelta(days=1), START, 7)
    with pytest.raises(ValueError):
        readiness(START.replace(tzinfo=None), START, START, 7)
