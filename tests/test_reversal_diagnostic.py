import pytest
from scripts.research.run_reversal_diagnostic import rows_for


def dataset(rows):
    return {"observed_at_utc": "2026-10-12T14:50:33+00:00", "markets": {
        "AVAX-USD": {"status": "GRID_VERIFIED", "raw_candles": {"candles": rows}}}}


def test_completed_window_excludes_current_day():
    end = 1791763200
    candles = [{"start": str(t), "open": "100", "high": "101", "low": "99",
                "close": "100", "volume": "1"}
               for t in range(end-182*86400, end+86400, 86400)]
    rows = rows_for(dataset(candles), "AVAX-USD")
    assert len(rows) == 182
    assert rows[-1][0] == (end-86400)*1000


def test_missing_history_is_not_filled():
    with pytest.raises(ValueError):
        rows_for(dataset([]), "AVAX-USD")
