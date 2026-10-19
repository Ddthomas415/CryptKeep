"""Regression contract probes for the active altcoin rerun; no archive/network use."""
import numpy as np

from scripts.research.rerun_frozen_altcoins import event_portfolio, summarize


def test_strict_pending_exit_stops_at_missing_held_candle():
    values = np.array([[100.], [100.], [100.], [float("nan")], [110.]])
    ns = {"C": values, "syms": ["TEST"], "D0": 0}
    result, _ = event_portfolio(ns, values, values, np.array([4]),
                                lambda k: [0] if k == 1 else [], lambda k, j: 1,
                                None, 0, 0, 0, 0, 4, "strict")
    assert result["status"] == "INCOMPLETE"


def test_low_touch_recovered_close_does_not_change_frozen_exit_signal():
    closes = np.full((5, 1), 100.)
    lows = closes.copy()
    lows[3, 0] = 50.
    ns = {"C": closes, "syms": ["TEST"], "D0": 0}
    result, _ = event_portfolio(ns, closes, lows, np.array([4]),
                                lambda k: [0] if k == 1 else [], lambda k, j: 1,
                                .35, 180, 0, 0, 0, 4, "strict")
    assert result["stop_exits"] == 0


def test_summary_benchmark_endpoint_matches_strategy_curve():
    result = summarize({}, [(0, 1000.), (1, 900.)],
                       [(0, 1000.), (1, 1100.), (2, 2000.)], 0)
    assert result["btc_end_marked_usd"] == 1100.


def test_close_trigger_fills_next_open_not_stop_threshold():
    closes = np.array([[100.], [100.], [100.], [60.], [40.]])
    ns = {"C": closes, "syms": ["TEST"], "D0": 0}
    result, _ = event_portfolio(ns, closes, closes, np.array([4]),
                                lambda k: [0] if k == 1 else [], lambda k, j: 1,
                                .35, 180, 0, 0, 0, 4, "strict")
    assert result["stop_exits"] == 1
    assert result["mean_trade_pct"] == -60.
    assert result["terminal_liquidated_at_last_close_usd"] == 940.


def test_entry_open_cannot_set_completed_close_peak():
    closes = np.full((5, 1), 100.)
    opens = closes.copy()
    opens[2, 0] = 200.
    ns = {"C": closes, "syms": ["TEST"], "D0": 0}
    result, _ = event_portfolio(ns, opens, closes, np.array([4]),
                                lambda k: [0] if k == 1 else [], lambda k, j: 1,
                                .35, 180, 0, 0, 0, 4, "strict")
    assert result["stop_exits"] == 0
