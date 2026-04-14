"""
services/control/canonical_strategy.py

Canonical strategy: daily 200-SMA trend following.

Rule:
  price > 200-day SMA → LONG
  price < 200-day SMA → FLAT

This is the reference strategy used to validate the control kernel.
It is simple enough to hold in one sentence, live-testable on any liquid market,
and rich enough to exercise all kernel branches (regime collapse, drawdown,
safe_degraded demotion).

Kernel integration:
  - All signals pass through ControlKernel.evaluate() before acting.
  - Allocation is kernel-controlled, not hard-coded.
  - No order is placed if the kernel says halt/restrict.
"""
from __future__ import annotations

from typing import Any

from services.control.kernel import ControlKernel, ACTION_HALT, ACTION_RESTRICT
from services.logging.app_logger import get_logger

_LOG = get_logger("control.canonical_strategy")

STRATEGY_ID = "canonical_200sma_trend"


def compute_signal(closes: list[float], *, period: int = 200) -> str:
    """Return 'long' or 'flat' based on 200-SMA rule.

    Args:
        closes: List of daily close prices, newest last.
        period: SMA period (default 200).

    Returns:
        'long' if price > SMA, 'flat' otherwise.
    """
    if len(closes) < period:
        return "flat"   # insufficient history
    sma = sum(closes[-period:]) / period
    current = closes[-1]
    return "long" if current > sma else "flat"


def decide(
    closes: list[float],
    *,
    kernel_metrics: dict[str, float] | None = None,
    risk_budget_usd: float = 100_000.0,
    contract_notional_usd: float = 5_000.0,
    period: int = 200,
) -> dict[str, Any]:
    """Full decision: signal + kernel gate + allocation.

    Args:
        closes:               Daily close prices, newest last.
        kernel_metrics:       Live execution/risk metrics for kernel evaluation.
        risk_budget_usd:      Total risk budget in USD.
        contract_notional_usd: Notional value per contract/unit.
        period:               SMA period.

    Returns:
        {
          "signal":           long | flat
          "kernel_action":    allow | derisk | restrict | halt
          "new_risk_allowed": bool
          "contracts":        int (0 if no new risk)
          "allocation_frac":  float
          "reasons":          list of trigger descriptions
          "stage":            deployment stage
        }
    """
    m = kernel_metrics or {}
    signal = compute_signal(closes, period=period)

    kernel = ControlKernel(STRATEGY_ID)
    decision = kernel.evaluate(m)

    contracts = 0
    if signal == "long" and decision["new_risk_allowed"]:
        contracts = kernel.contracts(risk_budget_usd, contract_notional_usd, m)

    result = {
        "signal":           signal,
        "kernel_action":    decision["action"],
        "new_risk_allowed": decision["new_risk_allowed"],
        "contracts":        contracts,
        "allocation_frac":  decision["allocation_frac"],
        "reasons":          decision["reasons"],
        "stage":            decision["stage"],
    }

    _LOG.info(
        "canonical_strategy signal=%s action=%s contracts=%s stage=%s reasons=%s",
        signal, decision["action"], contracts, decision["stage"], decision["reasons"]
    )
    return result


def regime_stability_from_sma(closes: list[float], *, period: int = 200,
                               lookback: int = 60) -> float:
    """Estimate regime stability: fraction of recent days where price > SMA.

    1.0 = perfectly stable trend, 0.0 = fully choppy/reversed.
    """
    if len(closes) < period + lookback:
        return 0.5
    scores = []
    for i in range(lookback):
        idx = -(lookback - i)
        window = closes[:idx] if idx != 0 else closes
        if len(window) < period:
            continue
        sma = sum(window[-period:]) / period
        scores.append(1.0 if window[-1] > sma else 0.0)
    return sum(scores) / len(scores) if scores else 0.5
