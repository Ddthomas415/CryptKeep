import pytest
from scripts.research.monday_market_diagnostic import DAY, day_summary


def test_monday_uses_next_open_and_excludes_current_incomplete_day():
    monday = 1775433600  # April 6, 2026, UTC Monday.
    rows = [{"start": str(monday), "open": "100"},
            {"start": str(monday+DAY), "open": "110"},
            {"start": str(monday+2*DAY), "open": "110"}]
    result = day_summary(rows, monday+DAY)
    assert result["monday"]["count"] == 1
    assert result["other_days"]["count"] == 0
    assert result["monday"]["mean_fee_adjusted_pct"] == pytest.approx((1.1*.995/1.005-1)*100)


def test_missing_next_day_is_not_filled_forward():
    assert day_summary([{"start": "1775433600", "open": "100"}], 1775433600+DAY)["monday"]["count"] == 0
