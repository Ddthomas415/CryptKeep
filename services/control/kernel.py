"""
services/control/kernel.py

The 8-component control kernel.

Integrates: deployment stage, cognitive budget, allocator, and safe_degraded
into a single entry point for the runtime loop.

Usage:
    from services.control.kernel import ControlKernel
    k = ControlKernel("my_strategy")
    decision = k.evaluate(metrics)
    if decision["action"] == "halt":
        ...
    elif decision["new_risk_allowed"]:
        contracts = k.contracts(risk_budget, contract_notional)

Components:
  1. Utility function (declared at top of this module)
  2. Deployment stage state machine
  3. Action primitives (allow / de-risk / restrict / halt)
  4. 6 invariant metrics
  5. Cognitive budget rule
  6. Safe-Degraded behavior
  7. State-aware allocator
  8. Termination gate (operator usability check)
"""
from __future__ import annotations

import math
from typing import Any

from services.control.deployment_stage import (
    Stage, get_current_stage, force_safe_degraded,
    action_allowed, stage_summary,
)
from services.control.cognitive_budget import (
    check_budget, record_alert, clear_alert,
)
from services.control.allocator import compute_allocation, allocation_summary
from services.logging.app_logger import get_logger, set_correlation_id

_LOG = get_logger("control.kernel")

# ---------------------------------------------------------------------------
# Utility function (declared, not computed — guides design decisions)
#
#   Maximize: long_term_return × (1 − ruin_risk)
#   Subject to: ruin_prob < 1%, max_dd < 25%, operator_time < 30 min/day avg
# ---------------------------------------------------------------------------

UTILITY_CONSTRAINTS = {
    "max_ruin_prob_pct":   1.0,
    "max_drawdown_pct":   25.0,
    "max_operator_min_per_day": 30.0,
}

# ---------------------------------------------------------------------------
# Metric thresholds (the 6 invariant metrics)
# ---------------------------------------------------------------------------

METRIC_THRESHOLDS = {
    "slippage_p95": {
        "warn":  0.5,   # 50% of expected edge consumed by slippage
        "crit":  1.0,   # slippage ≥ expected edge → halt
    },
    "fill_rate": {
        "warn":  0.92,  # below 92% fill rate → warn
        "crit":  0.80,  # below 80% → halt
    },
    "recon_drift": {
        "warn":  0.01,  # >1% drift between internal and broker → warn
        "crit":  0.05,  # >5% → halt
    },
    "dd_duration_days": {
        "warn":  30,    # in drawdown > 30 days → warn + de-risk
        "crit":  60,    # > 60 days → safe_degraded
    },
    "regime_stability": {
        "warn":  0.50,  # regime score < 50% → warn
        "crit":  0.25,  # < 25% → de-risk
    },
    "alert_count": {
        "warn":  3,
        "crit":  4,     # ≥ 4 active alerts → cognitive budget breach → safe_degraded
    },
}

# ---------------------------------------------------------------------------
# Action primitives
# ---------------------------------------------------------------------------

ACTION_ALLOW      = "allow"
ACTION_DERISK     = "derisk"     # reduce size 50%
ACTION_RESTRICT   = "restrict"   # reductions only
ACTION_HALT       = "halt"       # no new risk, no existing risk addition


def _action_severity(action: str) -> int:
    return {ACTION_ALLOW: 0, ACTION_DERISK: 1, ACTION_RESTRICT: 2, ACTION_HALT: 3}.get(action, 0)


def _worst_action(*actions: str) -> str:
    """Return the most severe action from a list."""
    return max(actions, key=_action_severity, default=ACTION_ALLOW)


# ---------------------------------------------------------------------------
# Kernel
# ---------------------------------------------------------------------------

class ControlKernel:
    """Single entry point for strategy control decisions."""

    def __init__(self, strategy_id: str) -> None:
        self.strategy_id = str(strategy_id)

    def evaluate(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Evaluate current metrics and return a control decision.

        Args:
            metrics: dict with keys matching METRIC_THRESHOLDS (all optional,
                     missing keys are treated as nominal/safe values).

        Returns:
            {
              "action":           allow | derisk | restrict | halt
              "stage":            current deployment stage
              "new_risk_allowed": bool
              "reasons":          list of trigger descriptions
              "allocation_frac":  float (0 if not allowed)
              "cognitive_budget": cognitive budget check result
            }
        """
        set_correlation_id(f"kernel:{self.strategy_id}")
        reasons: list[str] = []
        actions: list[str] = []
        stage = get_current_stage(self.strategy_id)

        # ---- Safe-Degraded: always halt ----
        if stage == Stage.SAFE_DEGRADED:
            return self._result(ACTION_HALT, stage, ["stage:safe_degraded"], metrics)

        # ---- Paper / Shadow: no new risk, but not a halt ----
        if stage in (Stage.PAPER, Stage.SHADOW):
            return self._result(ACTION_ALLOW, stage, [f"stage:{stage.value}_no_orders"], metrics)

        # ---- Evaluate each metric ----
        slip = float(metrics.get("slippage_p95") or 0.0)
        fill = float(metrics.get("fill_rate") or 1.0)
        recon = float(metrics.get("recon_drift") or 0.0)
        dd_days = float(metrics.get("dd_duration_days") or 0.0)
        regime = float(metrics.get("regime_stability") or 1.0)
        alerts = int(metrics.get("alert_count") or 0)

        t = METRIC_THRESHOLDS

        # Slippage
        if slip >= t["slippage_p95"]["crit"]:
            actions.append(ACTION_HALT)
            reasons.append(f"slippage_p95_crit:{slip:.2f}")
        elif slip >= t["slippage_p95"]["warn"]:
            actions.append(ACTION_DERISK)
            reasons.append(f"slippage_p95_warn:{slip:.2f}")

        # Fill rate
        if fill <= t["fill_rate"]["crit"]:
            actions.append(ACTION_HALT)
            reasons.append(f"fill_rate_crit:{fill:.2f}")
        elif fill <= t["fill_rate"]["warn"]:
            actions.append(ACTION_DERISK)
            reasons.append(f"fill_rate_warn:{fill:.2f}")

        # Reconciliation drift
        if recon >= t["recon_drift"]["crit"]:
            actions.append(ACTION_HALT)
            reasons.append(f"recon_drift_crit:{recon:.3f}")
        elif recon >= t["recon_drift"]["warn"]:
            actions.append(ACTION_RESTRICT)
            reasons.append(f"recon_drift_warn:{recon:.3f}")

        # Drawdown duration
        if dd_days >= t["dd_duration_days"]["crit"]:
            # Auto-demote to safe_degraded
            force_safe_degraded(
                self.strategy_id,
                reason=f"dd_duration_crit:{dd_days:.0f}d",
                actor="kernel",
            )
            actions.append(ACTION_HALT)
            reasons.append(f"dd_duration_crit:{dd_days:.0f}d→safe_degraded")
        elif dd_days >= t["dd_duration_days"]["warn"]:
            actions.append(ACTION_DERISK)
            reasons.append(f"dd_duration_warn:{dd_days:.0f}d")

        # Regime stability
        if regime <= t["regime_stability"]["crit"]:
            actions.append(ACTION_DERISK)
            reasons.append(f"regime_stability_crit:{regime:.2f}")
        elif regime <= t["regime_stability"]["warn"]:
            actions.append(ACTION_DERISK)
            reasons.append(f"regime_stability_warn:{regime:.2f}")

        # Cognitive budget (alert count)
        cb = check_budget(self.strategy_id, active_symbols=None)
        if alerts >= t["alert_count"]["crit"] or cb["breach"]:
            force_safe_degraded(
                self.strategy_id,
                reason=f"cognitive_budget_breach:alerts={alerts}",
                actor="kernel",
            )
            actions.append(ACTION_HALT)
            reasons.append(f"cognitive_budget_breach:alerts={alerts}→safe_degraded")
        elif alerts >= t["alert_count"]["warn"]:
            actions.append(ACTION_RESTRICT)
            reasons.append(f"alert_count_warn:{alerts}")

        final_action = _worst_action(*actions) if actions else ACTION_ALLOW
        return self._result(final_action, stage, reasons or ["nominal"], metrics)

    def _result(self, action: str, stage: Stage, reasons: list[str],
                metrics: dict[str, float]) -> dict[str, Any]:
        new_risk = action == ACTION_ALLOW and stage not in (
            Stage.PAPER, Stage.SHADOW, Stage.SAFE_DEGRADED
        )
        alloc = 0.0
        if new_risk:
            regime = float(metrics.get("regime_stability") or 1.0)
            slip = float(metrics.get("slippage_p95") or 0.0)
            dd_days = float(metrics.get("dd_duration_days") or 0.0)
            drift_penalty = min(1.0, slip)
            dd_frac = min(1.0, dd_days / max(1, METRIC_THRESHOLDS["dd_duration_days"]["crit"]))
            alloc = compute_allocation(
                self.strategy_id,
                regime_stability=regime,
                drift_penalty=drift_penalty,
                drawdown_frac=dd_frac,
            )
            if alloc <= 0:
                new_risk = False

        return {
            "action":           action,
            "stage":            get_current_stage(self.strategy_id).value,
            "new_risk_allowed": new_risk,
            "allocation_frac":  alloc,
            "reasons":          reasons,
            "cognitive_budget": check_budget(self.strategy_id),
        }

    def contracts(self, risk_budget_usd: float, contract_notional_usd: float,
                  metrics: dict[str, float] | None = None) -> int:
        """Return max contracts to trade given current allocation."""
        m = metrics or {}
        dec = self.evaluate(m)
        if not dec["new_risk_allowed"]:
            return 0
        alloc_usd = dec["allocation_frac"] * risk_budget_usd
        n = math.floor(alloc_usd / max(1.0, contract_notional_usd))
        # Stage cap for capped_live
        if get_current_stage(self.strategy_id) == Stage.CAPPED_LIVE:
            n = min(n, 1)
        return max(0, n)

    def status(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "stage": stage_summary(self.strategy_id),
            "cognitive_budget": check_budget(self.strategy_id),
        }
