"""
services/strategies/strategy_name.py
=====================================
Canonical strategy name normalization.

**Single source of truth** for mapping raw strategy identifiers (from
exchange fills, config files, pipeline labels, or external signals) to
the normalized strategy keys used throughout the evidence, leaderboard,
and analytics pipeline.

Previously duplicated across three independent modules:
  - services/backtest/evidence_cycle.py
  - services/backtest/evidence_shared.py
  - services/analytics/strategy_feedback.py

All three now import from here.
"""

from __future__ import annotations

from typing import Any


KNOWN_STRATEGIES: frozenset[str] = frozenset(
    {
        "ema_cross",
        "mean_reversion_rsi",
        "breakout_donchian",
        "momentum",
        "sma_200_trend",
    }
)


def normalize_strategy_name(value: Any) -> str | None:
    """
    Map a raw strategy identifier to its canonical key.

    Returns None when the value cannot be mapped, which causes the
    fill to be counted in unmapped_strategy_ids for review.
    """
    text = str(value or "").strip().lower()
    if not text:
        return None

    # Fast path: already canonical
    if text in KNOWN_STRATEGIES:
        return text

    # EMA crossover variants
    if "ema" in text and ("cross" in text or "xover" in text or "crossover" in text):
        return "ema_cross"

    # Mean reversion variants
    if "mean_reversion" in text or "mean-reversion" in text or "reversion" in text:
        return "mean_reversion_rsi"

    # Breakout / Donchian variants
    if "breakout" in text or "donchian" in text:
        return "breakout_donchian"

    # ES Daily Trend / SMA-200 variants
    if "sma_200" in text or "es_daily_trend" in text or "daily_trend" in text:
        return "sma_200_trend"

    return None
