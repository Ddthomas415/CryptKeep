"""
services/control/allocator.py

State-aware capital allocator.

Allocation is a function of:
  - deployment stage (hard cap)
  - regime stability score (0-1)
  - drift penalty (slippage vs baseline)
  - drawdown state

Formula:
  allocation = base_weight × stability × (1 − drift_penalty) × regime_factor
  clamped to [0, stage_max_alloc]

Returns 0.0 for paper/shadow/safe_degraded regardless of inputs.

Usage:
    from services.control.allocator import compute_allocation
    frac = compute_allocation("my_strategy", regime_stability=0.8, drift_penalty=0.1, ...)
    contracts = int(frac * risk_budget / contract_notional)
"""
from __future__ import annotations

from typing import Any

from services.control.deployment_stage import get_current_stage, Stage, max_allocation_frac
from services.logging.app_logger import get_logger

_LOG = get_logger("control.allocator")

# Base weight: fraction of total risk budget per strategy slot
DEFAULT_BASE_WEIGHT = 0.10   # 10% of risk budget per strategy (before adjustments)

# Minimum allocation below which we treat as zero (avoid tiny fractions)
MIN_MEANINGFUL_ALLOC = 0.005


def compute_allocation(
    strategy_id: str,
    *,
    regime_stability: float = 1.0,
    drift_penalty: float = 0.0,
    drawdown_frac: float = 0.0,
    base_weight: float = DEFAULT_BASE_WEIGHT,
) -> float:
    """Return allocation fraction of risk budget for new risk.

    Args:
        strategy_id:       Which strategy to compute for.
        regime_stability:  0.0 (poor) to 1.0 (stable). Reduces allocation.
        drift_penalty:     0.0 (no drift) to 1.0 (severe). Reduces allocation.
        drawdown_frac:     Current drawdown as fraction of max_dd limit (0–1).
                           At 1.0 (at limit) allocation goes to zero.
        base_weight:       Base fraction of risk budget before adjustments.

    Returns:
        Allocation fraction in [0.0, stage_max_alloc].
    """
    stage = get_current_stage(strategy_id)

    # Stages that never get new risk — return immediately
    if stage in (Stage.PAPER, Stage.SHADOW, Stage.SAFE_DEGRADED):
        return 0.0

    stage_cap = max_allocation_frac(strategy_id)
    if stage_cap <= 0:
        return 0.0

    # Stability factor: clamp 0-1
    stab = max(0.0, min(1.0, float(regime_stability)))

    # Drift penalty: 0 = no penalty, 1 = full reduction
    drift = max(0.0, min(1.0, float(drift_penalty)))

    # Drawdown factor: linear reduction from 1.0 at dd=0 to 0.0 at dd=1.0
    dd = max(0.0, min(1.0, float(drawdown_frac)))
    dd_factor = max(0.0, 1.0 - dd)

    raw = base_weight * stab * (1.0 - drift) * dd_factor
    clamped = max(0.0, min(stage_cap, raw))

    # Treat tiny fractions as zero
    result = clamped if clamped >= MIN_MEANINGFUL_ALLOC else 0.0

    _LOG.debug(
        "allocator strategy=%s stage=%s stab=%.2f drift=%.2f dd=%.2f raw=%.4f result=%.4f",
        strategy_id, stage.value, stab, drift, dd, raw, result,
    )
    return result


def allocation_summary(
    strategy_id: str,
    *,
    regime_stability: float = 1.0,
    drift_penalty: float = 0.0,
    drawdown_frac: float = 0.0,
) -> dict[str, Any]:
    """Human-readable allocation breakdown for dashboards/logs."""
    stage = get_current_stage(strategy_id)
    frac = compute_allocation(
        strategy_id,
        regime_stability=regime_stability,
        drift_penalty=drift_penalty,
        drawdown_frac=drawdown_frac,
    )
    return {
        "strategy_id": strategy_id,
        "stage": stage.value,
        "allocation_frac": frac,
        "stage_cap_frac": max_allocation_frac(strategy_id),
        "regime_stability": regime_stability,
        "drift_penalty": drift_penalty,
        "drawdown_frac": drawdown_frac,
        "new_risk_allowed": frac > 0,
    }
