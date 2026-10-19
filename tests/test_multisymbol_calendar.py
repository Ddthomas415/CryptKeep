import math

import numpy as np
import pytest

from scripts.research.report_multisymbol_calendar import (
    DAY, HOUR, aggregate, block_indices, daily_rows, diagnostics, drawdowns,
)


def fixture():
    return {"equity": [{"bar_ts_ms": i*HOUR, "equity_quote": 1000+i}
                       for i in range(48)],
            "terminal_equity_quote": 1045., "net_quote_profit": 45.}


def test_midnight_and_terminal_cost_belong_to_day_just_ended():
    rows = daily_rows(fixture(), start=0, end=2*DAY, capital=1000)
    assert [r["date"] for r in rows] == ["1970-01-01", "1970-01-02"]
    assert [r["net_quote_change"] for r in rows] == [23, 22]
    assert aggregate(rows)[0]["net_quote_change"] == 45
    assert sum(r["net_quote_change"] for r in aggregate(rows, weekly=True)) == 45


@pytest.mark.parametrize("kind", ["gap", "missing", "nan", "negative", "total"])
def test_invalid_equity_refused(kind):
    result = fixture()
    if kind == "gap": result["equity"][1]["bar_ts_ms"] = 2*HOUR
    if kind == "missing": result["equity"].pop()
    if kind == "nan": result["equity"][1]["equity_quote"] = math.nan
    if kind == "negative": result["terminal_equity_quote"] = -1
    if kind == "total": result["net_quote_profit"] = 90
    with pytest.raises(ValueError):
        daily_rows(result, start=0, end=2*DAY, capital=1000)


def test_circular_indices_reproducible_contiguous_and_bounded():
    idx = block_indices(9, 4, reps=10, seed=1)
    assert np.array_equal(idx, block_indices(9, 4, reps=10, seed=1))
    assert idx.shape == (10, 9) and idx.min() >= 0 and idx.max() < 9
    assert np.all((idx[:, 1:4]-idx[:, :3]) % 9 == 1)


def test_constant_paths_and_pairing():
    idx = block_indices(12, 3, reps=20)
    result = diagnostics([1.]*12, [1.]*12, idx, 1000)
    assert result["net_quote_profit_percentile_95"] == [12, 12]
    assert result["net_quote_gap_vs_buy_hold_percentile_95"] == [0, 0]
    assert result["drawdown_pct_gap_vs_buy_hold_percentile_95"] == [0, 0]
    assert drawdowns([-100, 50], 1000)[0] == pytest.approx(10)


def test_month_and_iso_week_boundaries_preserve_totals():
    rows = [{"date": date, "net_quote_change": amount,
             "start_equity_quote": 1000, "end_equity_quote": 1000+amount}
            for date, amount in [("2025-12-31", 1), ("2026-01-01", 2)]]
    assert [r["period"] for r in aggregate(rows)] == ["2025-12", "2026-01"]
    assert aggregate(rows, weekly=True)[0]["period"] == "2026-W01"
    assert aggregate(rows, weekly=True)[0]["net_quote_change"] == 3


def test_unpaired_or_invalid_resampled_paths_refused():
    with pytest.raises(ValueError):
        diagnostics([1, 2], [1], np.array([[0, 1]]), 1000)
    with pytest.raises(ValueError):
        drawdowns([-1100], 1000)
