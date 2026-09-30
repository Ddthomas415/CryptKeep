"""Research-only next-open signal schedule, not fills or profitability."""
from services.strategies.daily_crossover import DAY_MS, POLICY
from services.strategies.strategy_registry import compute_signal


def schedule(rows, *, sma_period=200):
    """Use only rows preceding each candidate execution bar's open.

    A BUY is an eligible crossover, not evidence that risk approved or filled it.
    No execution-bar prices enter signal computation.
    """
    result = []
    for i in range(sma_period + 1, len(rows)):
        now = rows[i][0]
        if type(now) is not int or now != rows[i-1][0] + DAY_MS:
            raise ValueError("invalid_next_open_timestamp")
        signal = compute_signal(cfg={"strategy": {
            "name": "sma_200_trend", "sma_period": sma_period,
            "entry_policy": POLICY, "decision_time_ms": now,
            "emit_evidence": False,
        }}, symbol="BTC/USDT", ohlcv=rows[:i])
        if not signal.get("ok"):
            raise ValueError("invalid_completed_history")
        result.append({"decision_time_ms": now, "signal": signal,
                       "evidence_kind": "MODELLED_SIGNAL_NOT_FILL"})
    return result
