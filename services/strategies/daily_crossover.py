"""Shared completed-daily-bar entry contract for runtime and research."""
import math

POLICY = "completed_daily_crossover_v1"
DAY_MS = 86_400_000


def completed_crossover(rows, *, decision_time_ms, period=200):
    if type(decision_time_ms) is not int or decision_time_ms <= 0:
        raise ValueError("decision_time_required")
    if type(period) is not int or period < 2:
        raise ValueError("invalid_sma_period")
    completed = []
    previous = None
    for row in rows:
        if len(row) != 6 or type(row[0]) is not int or row[0] % DAY_MS:
            raise ValueError("invalid_daily_bar")
        ts, op, high, low, close, volume = row
        if previous is not None and ts - previous != DAY_MS:
            raise ValueError("noncontiguous_daily_bars")
        previous = ts
        if not all(math.isfinite(v) and v > 0 for v in (op, high, low, close)):
            raise ValueError("invalid_prices")
        if not low <= min(op, close) <= max(op, close) <= high:
            raise ValueError("invalid_ohlc")
        if not math.isfinite(volume) or volume < 0:
            raise ValueError("invalid_volume")
        if ts > decision_time_ms:
            raise ValueError("future_bar")
        if ts + DAY_MS <= decision_time_ms:
            completed.append(row)
    expected = decision_time_ms // DAY_MS * DAY_MS - DAY_MS
    if len(completed) < period + 1 or completed[-1][0] != expected:
        raise ValueError("insufficient_or_stale_completed_history")
    closes = [r[4] for r in completed[-period-1:]]
    prior_sma = sum(closes[:-1]) / period
    current_sma = sum(closes[1:]) / period
    return completed, closes[-2] <= prior_sma and closes[-1] > current_sma
