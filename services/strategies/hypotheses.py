from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


HYPOTHESES: Dict[str, Dict[str, Any]] = {
    "ema_cross": {
        "strategy": "ema_cross",
        "market_assumption": "Directional moves persist after a confirmed fast/slow EMA crossover when range and participation are not collapsing.",
        "required_data": ["ohlcv.close", "ohlcv.high", "ohlcv.low", "ohlcv.volume"],
        "entry_rules": [
            "Buy when fast EMA crosses above slow EMA.",
            "Sell when fast EMA crosses below slow EMA.",
            "Require volatility, relative volume, cross-gap, and trend-consensus filters when configured.",
        ],
        "exit_rules": [
            "Exit or reverse on the opposite EMA crossover.",
        ],
        "no_trade_rules": [
            "Do not trade in low-volatility tape.",
            "Do not trade when relative volume is too weak.",
            "Do not trade when trend efficiency implies chop.",
            "Do not trade when the crossover gap is too small to confirm.",
        ],
        "invalidation_conditions": [
            "Price is on the wrong side of the slow EMA for the proposed direction.",
            "Slow EMA slope disagrees with the signal direction.",
            "Confirmation filters fail on the triggering bar.",
        ],
        "expected_failure_regimes": ["chop", "low_vol", "event_reversal"],
        "notes": [
            "This is a trend-following hypothesis, not a proven edge.",
            "Sell signals are part of the shared strategy contract and are not a claim of validated short support.",
        ],
    },
    "mean_reversion_rsi": {
        "strategy": "mean_reversion_rsi",
        "market_assumption": "Short-term oversold and overbought moves revert toward a moving average when the market is not in a one-way panic or squeeze.",
        "required_data": ["ohlcv.close", "ohlcv.high", "ohlcv.low", "ohlcv.volume", "rsi", "sma"],
        "entry_rules": [
            "Buy when RSI is below the configured buy threshold and price is below the SMA.",
            "Sell when RSI is above the configured sell threshold and price is above the SMA.",
            "Optionally require reversal confirmation before acting.",
        ],
        "exit_rules": [
            "Exit or reverse when the opposite RSI/SMA extreme appears.",
        ],
        "no_trade_rules": [
            "Do not trade during high-volatility conditions.",
            "Do not trade when relative volume is too weak.",
            "Do not trade when the recent move is too one-sided.",
            "Do not trade when price is too far from the SMA to justify a controlled reversion bet.",
        ],
        "invalidation_conditions": [
            "Price continues to move away from the SMA without reversal confirmation.",
            "Volatility expands beyond the configured tolerance.",
            "Trend efficiency remains too strong for a reversion setup.",
        ],
        "expected_failure_regimes": ["bear", "bull", "high_vol", "event_trend"],
        "notes": [
            "This is a controlled countertrend hypothesis, not proof that reversions persist.",
            "Sell signals are part of the shared strategy contract and are not a claim of validated short support.",
        ],
    },
    "breakout_donchian": {
        "strategy": "breakout_donchian",
        "market_assumption": "A move outside a meaningful Donchian channel can continue when the breakout arrives with enough range and participation.",
        "required_data": ["ohlcv.close", "ohlcv.high", "ohlcv.low", "ohlcv.volume", "donchian_channel"],
        "entry_rules": [
            "Buy when price breaks above the previous upper Donchian band.",
            "Sell when price breaks below the previous lower Donchian band.",
            "Optionally require a breakout buffer and directional confirmation.",
        ],
        "exit_rules": [
            "Exit or reverse on the opposite Donchian breakout.",
        ],
        "no_trade_rules": [
            "Do not trade when volatility is too low.",
            "Do not trade when relative volume is too weak.",
            "Do not trade when trend efficiency still reads as chop.",
            "Do not trade when the prior channel width is too narrow to matter.",
        ],
        "invalidation_conditions": [
            "The breakout fails directional confirmation on the trigger bar.",
            "Channel width is too narrow to justify a continuation thesis.",
            "Confirmation filters fail on the proposed breakout bar.",
        ],
        "expected_failure_regimes": ["chop", "low_vol", "thin_liquidity", "false_breakout"],
        "notes": [
            "This is a continuation hypothesis, not proof that breakouts persist.",
            "Sell signals are part of the shared strategy contract and are not a claim of validated short support.",
        ],
    },
}


def get_strategy_hypothesis(name: str) -> Dict[str, Any] | None:
    item = HYPOTHESES.get(str(name or "").strip())
    return deepcopy(item) if item is not None else None


def list_strategy_hypotheses() -> list[Dict[str, Any]]:
    return [deepcopy(HYPOTHESES[name]) for name in sorted(HYPOTHESES.keys())]
