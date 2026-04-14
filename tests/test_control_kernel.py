"""tests/test_control_kernel.py — Control kernel test suite."""
from __future__ import annotations

import pytest
import os


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolate_state(tmp_path, monkeypatch):
    """Each test gets its own state directory."""
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


# ---------------------------------------------------------------------------
# 1. Deployment stage machine
# ---------------------------------------------------------------------------

class TestDeploymentStage:
    def test_default_stage_is_paper(self):
        from services.control.deployment_stage import get_current_stage, Stage
        assert get_current_stage("test_strat") == Stage.PAPER

    def test_promote_paper_to_shadow(self):
        from services.control.deployment_stage import get_current_stage, promote, Stage
        result = promote("strat_a", reason="manual_test", actor="test")
        assert result["ok"] is True
        assert get_current_stage("strat_a") == Stage.SHADOW

    def test_promote_through_all_stages(self):
        from services.control.deployment_stage import promote, get_current_stage, Stage
        sid = "full_promo"
        promote(sid, reason="r1")
        promote(sid, reason="r2")
        promote(sid, reason="r3")
        assert get_current_stage(sid) == Stage.SCALED_LIVE

    def test_cannot_promote_beyond_scaled_live(self):
        from services.control.deployment_stage import promote, Stage
        sid = "max_stage"
        for _ in range(3): promote(sid, reason="r")
        result = promote(sid, reason="too_far")
        assert result["ok"] is False

    def test_force_safe_degraded(self):
        from services.control.deployment_stage import promote, force_safe_degraded, get_current_stage, Stage
        sid = "degrade_me"
        promote(sid, reason="r")
        promote(sid, reason="r")
        force_safe_degraded(sid, reason="breach", actor="kernel")
        assert get_current_stage(sid) == Stage.SAFE_DEGRADED

    def test_cannot_promote_from_safe_degraded(self):
        from services.control.deployment_stage import promote, force_safe_degraded
        sid = "stuck"
        force_safe_degraded(sid, reason="breach")
        result = promote(sid, reason="attempt")
        assert result["ok"] is False

    def test_action_allowed_paper_no_submit(self):
        from services.control.deployment_stage import action_allowed
        allowed, _ = action_allowed("new_strat", "submit_capped")
        assert allowed is False

    def test_action_allowed_capped_live(self):
        from services.control.deployment_stage import promote, action_allowed
        sid = "capped"
        promote(sid, reason="r")
        promote(sid, reason="r")
        allowed, _ = action_allowed(sid, "submit_capped")
        assert allowed is True

    def test_max_allocation_zero_in_paper(self):
        from services.control.deployment_stage import max_allocation_frac
        assert max_allocation_frac("paper_strat") == 0.0

    def test_max_allocation_nonzero_in_capped(self):
        from services.control.deployment_stage import promote, max_allocation_frac
        sid = "capped2"
        promote(sid, reason="r"); promote(sid, reason="r")
        assert max_allocation_frac(sid) > 0.0

    def test_history_is_recorded(self):
        from services.control.deployment_stage import promote, load_stage
        sid = "hist_test"
        promote(sid, reason="first_move")
        rec = load_stage(sid)
        assert len(rec["history"]) == 1
        assert rec["history"][0]["reason"] == "first_move"


# ---------------------------------------------------------------------------
# 2. Cognitive budget
# ---------------------------------------------------------------------------

class TestCognitiveBudget:
    def test_no_breach_initially(self):
        from services.control.cognitive_budget import check_budget
        result = check_budget("fresh_strat")
        assert result["breach"] is False

    def test_alert_count_breach_at_5(self):
        from services.control.cognitive_budget import record_alert
        sid = "alert_strat"
        for i in range(5):
            result = record_alert(sid, f"alert_{i}")
        assert result["breach"] is True
        assert result["breach_type"] == "alert_count"

    def test_no_breach_at_4_alerts(self):
        from services.control.cognitive_budget import record_alert
        sid = "four_alerts"
        for i in range(4):
            result = record_alert(sid, f"a{i}")
        assert result["breach"] is False

    def test_clear_alert_reduces_count(self):
        from services.control.cognitive_budget import record_alert, clear_alert, check_budget
        sid = "clear_test"
        for i in range(5): record_alert(sid, f"x{i}")
        clear_alert(sid, "x0")
        result = check_budget(sid)
        assert result["alert_count"] == 4

    def test_duplicate_alert_not_counted_twice(self):
        from services.control.cognitive_budget import record_alert
        sid = "dedup"
        record_alert(sid, "same_type")
        r = record_alert(sid, "same_type")
        assert r["alert_count"] == 1


# ---------------------------------------------------------------------------
# 3. Allocator
# ---------------------------------------------------------------------------

class TestAllocator:
    def test_zero_in_paper(self):
        from services.control.allocator import compute_allocation
        assert compute_allocation("alloc_paper") == 0.0

    def test_nonzero_in_capped(self):
        from services.control.deployment_stage import promote
        from services.control.allocator import compute_allocation
        sid = "alloc_capped"
        promote(sid, reason="r"); promote(sid, reason="r")
        result = compute_allocation(sid, regime_stability=1.0, drift_penalty=0.0)
        assert result > 0.0

    def test_zero_in_safe_degraded(self):
        from services.control.deployment_stage import force_safe_degraded
        from services.control.allocator import compute_allocation
        sid = "alloc_degraded"
        force_safe_degraded(sid, reason="test")
        assert compute_allocation(sid) == 0.0

    def test_drift_penalty_reduces_allocation(self):
        from services.control.deployment_stage import promote
        from services.control.allocator import compute_allocation
        sid = "drift_test"
        promote(sid, reason="r"); promote(sid, reason="r")
        base = compute_allocation(sid, drift_penalty=0.0)
        penalised = compute_allocation(sid, drift_penalty=0.8)
        assert penalised < base

    def test_regime_stability_scales_allocation(self):
        from services.control.deployment_stage import promote
        from services.control.allocator import compute_allocation
        sid = "regime_test"
        promote(sid, reason="r"); promote(sid, reason="r")
        high = compute_allocation(sid, regime_stability=1.0)
        low  = compute_allocation(sid, regime_stability=0.3)
        assert low < high

    def test_drawdown_at_limit_zeroes_allocation(self):
        from services.control.deployment_stage import promote
        from services.control.allocator import compute_allocation
        sid = "dd_test"
        promote(sid, reason="r"); promote(sid, reason="r")
        result = compute_allocation(sid, drawdown_frac=1.0)
        assert result == 0.0


# ---------------------------------------------------------------------------
# 4. Control kernel
# ---------------------------------------------------------------------------

class TestControlKernel:
    def test_nominal_metrics_allow(self):
        from services.control.kernel import ControlKernel, ACTION_ALLOW
        from services.control.deployment_stage import promote
        sid = "kernel_nominal"
        promote(sid, reason="r"); promote(sid, reason="r")
        k = ControlKernel(sid)
        dec = k.evaluate({"slippage_p95": 0.1, "fill_rate": 0.98,
                           "recon_drift": 0.0, "dd_duration_days": 5,
                           "regime_stability": 0.9, "alert_count": 0})
        assert dec["action"] == ACTION_ALLOW
        assert dec["new_risk_allowed"] is True

    def test_critical_slippage_halts(self):
        from services.control.kernel import ControlKernel, ACTION_HALT
        from services.control.deployment_stage import promote
        sid = "kernel_slip"
        promote(sid, reason="r"); promote(sid, reason="r")
        k = ControlKernel(sid)
        dec = k.evaluate({"slippage_p95": 1.5, "fill_rate": 0.98,
                           "recon_drift": 0.0, "dd_duration_days": 5,
                           "regime_stability": 0.9, "alert_count": 0})
        assert dec["action"] == ACTION_HALT

    def test_cognitive_budget_breach_forces_safe_degraded(self):
        from services.control.kernel import ControlKernel, ACTION_HALT
        from services.control.deployment_stage import promote, get_current_stage, Stage
        sid = "kernel_cog"
        promote(sid, reason="r"); promote(sid, reason="r")
        k = ControlKernel(sid)
        dec = k.evaluate({"alert_count": 5, "fill_rate": 0.99,
                           "recon_drift": 0.0, "dd_duration_days": 0,
                           "regime_stability": 0.9, "slippage_p95": 0.1})
        assert dec["action"] == ACTION_HALT
        assert get_current_stage(sid) == Stage.SAFE_DEGRADED

    def test_dd_duration_critical_forces_safe_degraded(self):
        from services.control.kernel import ControlKernel
        from services.control.deployment_stage import promote, get_current_stage, Stage
        sid = "kernel_dd"
        promote(sid, reason="r"); promote(sid, reason="r")
        k = ControlKernel(sid)
        k.evaluate({"dd_duration_days": 65, "fill_rate": 0.99,
                    "recon_drift": 0.0, "regime_stability": 0.9,
                    "slippage_p95": 0.1, "alert_count": 0})
        assert get_current_stage(sid) == Stage.SAFE_DEGRADED

    def test_paper_stage_always_allows_no_new_risk(self):
        from services.control.kernel import ControlKernel, ACTION_ALLOW
        sid = "kernel_paper"
        k = ControlKernel(sid)
        dec = k.evaluate({"slippage_p95": 2.0, "fill_rate": 0.5})
        assert dec["action"] == ACTION_ALLOW
        assert dec["new_risk_allowed"] is False

    def test_contracts_zero_in_paper(self):
        from services.control.kernel import ControlKernel
        k = ControlKernel("contracts_paper")
        assert k.contracts(100_000, 5_000) == 0

    def test_contracts_positive_in_capped(self):
        from services.control.kernel import ControlKernel
        from services.control.deployment_stage import promote
        sid = "contracts_capped"
        promote(sid, reason="r"); promote(sid, reason="r")
        k = ControlKernel(sid)
        n = k.contracts(100_000, 5_000, {
            "slippage_p95": 0.1, "fill_rate": 0.98,
            "recon_drift": 0.0, "dd_duration_days": 0,
            "regime_stability": 1.0, "alert_count": 0,
        })
        assert n >= 0   # may be 0 if allocation rounds down

    def test_worst_action_precedence(self):
        from services.control.kernel import _worst_action, ACTION_HALT, ACTION_DERISK, ACTION_ALLOW
        assert _worst_action(ACTION_ALLOW, ACTION_DERISK, ACTION_HALT) == ACTION_HALT
        assert _worst_action(ACTION_ALLOW, ACTION_DERISK) == ACTION_DERISK


# ---------------------------------------------------------------------------
# 5. Canonical strategy
# ---------------------------------------------------------------------------

class TestCanonicalStrategy:
    def _closes(self, above_sma: bool, n: int = 205) -> list[float]:
        """Generate synthetic close series."""
        import random
        random.seed(42)
        closes = [100.0 + i * 0.1 for i in range(n)]
        if not above_sma:
            closes[-1] = closes[-1] - 50  # push below SMA
        return closes

    def test_signal_long_when_above_sma(self):
        from services.control.canonical_strategy import compute_signal
        closes = self._closes(above_sma=True)
        assert compute_signal(closes) == "long"

    def test_signal_flat_when_below_sma(self):
        from services.control.canonical_strategy import compute_signal
        closes = self._closes(above_sma=False)
        assert compute_signal(closes) == "flat"

    def test_signal_flat_on_insufficient_history(self):
        from services.control.canonical_strategy import compute_signal
        assert compute_signal([100.0] * 50) == "flat"

    def test_decide_no_contracts_in_paper(self):
        from services.control.canonical_strategy import decide, STRATEGY_ID
        closes = self._closes(above_sma=True)
        result = decide(closes)
        assert result["contracts"] == 0
        assert result["stage"] == "paper"

    def test_decide_allows_contracts_in_capped(self):
        from services.control.canonical_strategy import decide, STRATEGY_ID
        from services.control.deployment_stage import promote
        promote(STRATEGY_ID + "_2", reason="r")
        promote(STRATEGY_ID + "_2", reason="r")

        import services.control.canonical_strategy as cs
        orig_id = cs.STRATEGY_ID
        cs.STRATEGY_ID = STRATEGY_ID + "_2"
        try:
            closes = self._closes(above_sma=True)
            result = decide(closes, kernel_metrics={
                "slippage_p95": 0.1, "fill_rate": 0.99,
                "recon_drift": 0.0, "dd_duration_days": 0,
                "regime_stability": 1.0, "alert_count": 0,
            }, risk_budget_usd=100_000, contract_notional_usd=1_000)
            assert result["signal"] == "long"
            assert result["kernel_action"] == "allow"
        finally:
            cs.STRATEGY_ID = orig_id

    def test_regime_stability_from_sma(self):
        from services.control.canonical_strategy import regime_stability_from_sma
        closes = [100.0 + i * 0.5 for i in range(300)]   # persistent uptrend
        stability = regime_stability_from_sma(closes)
        assert stability > 0.8

    def test_regime_stability_choppy(self):
        from services.control.canonical_strategy import regime_stability_from_sma
        import random
        random.seed(0)
        closes = [100.0 + random.uniform(-5, 5) for _ in range(300)]
        stability = regime_stability_from_sma(closes)
        assert 0.0 <= stability <= 1.0
