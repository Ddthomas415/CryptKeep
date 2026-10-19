from datetime import datetime, timedelta, timezone

import pytest
from zoneinfo import ZoneInfo

from scripts.research.cmc_endpoint_timing import select_endpoint

ENTRY = datetime(2026, 10, 9, 13, 52, tzinfo=timezone.utc)


@pytest.mark.parametrize("horizon", [1, 7, 30])
def test_exact_registered_horizon(horizon):
    target = ENTRY + timedelta(days=horizon)
    result = select_endpoint(ENTRY, horizon, [(target, "snapshot")])
    assert result["status"] == "SELECTED"
    assert result["elapsed_seconds"] == horizon * 86400
    assert result["deviation_seconds"] == 0


def test_boundary_inclusive_and_earlier_tie():
    target = ENTRY + timedelta(days=7)
    early, late = target - timedelta(hours=12), target + timedelta(hours=12)
    assert select_endpoint(ENTRY, 7, [(late, "late"), (early, "early")])["reference"] == "early"


def test_missing_not_extended_or_replaced_with_entry():
    target = ENTRY + timedelta(days=1)
    observations = [(ENTRY, "entry"), (target + timedelta(hours=12, microseconds=1), "late")]
    assert select_endpoint(ENTRY, 1, observations)["status"] == "MISSING"
    assert select_endpoint(ENTRY, 30, []) ["status"] == "MISSING"


def test_duplicate_and_naive_times_refused():
    target = ENTRY + timedelta(days=7)
    with pytest.raises(ValueError):
        select_endpoint(ENTRY, 7, [(target, "a"), (target, "b")])
    with pytest.raises(ValueError):
        select_endpoint(ENTRY, 7, [(target.replace(tzinfo=None), "a")])
    with pytest.raises(ValueError):
        select_endpoint(ENTRY.replace(tzinfo=None), 7, [])


def test_invalid_horizon_refused():
    with pytest.raises(ValueError):
        select_endpoint(ENTRY, 2, [])


@pytest.mark.parametrize("month,day", [(10, 31), (3, 7)])
def test_dst_uses_elapsed_utc_days(month, day):
    entry = datetime(2026, month, day, 13, tzinfo=ZoneInfo("America/New_York"))
    target = entry.astimezone(timezone.utc) + timedelta(days=1)
    result = select_endpoint(entry, 1, [(target.astimezone(entry.tzinfo), "exact")])
    assert result["elapsed_seconds"] == 86400
    assert result["deviation_seconds"] == 0
    assert result["target_time"] == target
