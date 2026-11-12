"""Synthetic-only reproduction of the remaining invalid-input recording gap."""
import json
import math
from tests.test_runner_decision_capture import make_record
from services.market_data.hourly_candle_quality import assess_hourly_candles
from services.strategies.signal_input_capture import capture_runner_decision

record = make_record()
record["ohlcv"][-1][4] = float("nan")
record["candle_quality"] = assess_hourly_candles(record["ohlcv"], now=record["observed_at"])
print(json.dumps({"synthetic_only": True, "last_close_is_nan": math.isnan(record["ohlcv"][-1][4]),
    "quality_reason": record["candle_quality"]["reason"], "quality_ok": record["candle_quality"]["ok"],
    "capture_result": capture_runner_decision(record)}, sort_keys=True))
