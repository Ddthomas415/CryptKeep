"""tests/test_allocator.py

Tests for services/control/allocator.py — capital allocation formula.

The formula is: base_weight × stability × (1 − drift) × (1 − dd_frac)
clamped to [0, stage_cap].

Paper/shadow/safe_degraded always return 0.0.
Capped_live cap is 0.05 (5%).
"""
from __future__ import annotations
import pytest
from services.control.allocator import compute_allocation, allocation_summary, DEFAULT_BASE_WEIGHT, MIN_MEANINGFUL_ALLOC
from services.control.deployment_stage import promote, force_safe_degraded, Stage

SID = "test_alloc"


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


def _promote_to_capped():
    promote(SID, reason="to_shadow", actor="test")
    promote(SID, reason="to_capped", actor="test")


class TestZeroStages:
    def test_paper_returns_zero(self):
        assert compute_allocation(SID) == 0.0

    def test_shadow_returns_zero(self):
        promote(SID, reason="up", actor="test")
        assert compute_allocation(SID) == 0.0

    def test_safe_degraded_returns_zero(self):
        force_safe_degraded(SID, reason="test", actor="test")
        assert compute_allocation(SID) == 0.0


class TestCappedLiveFormula:
    def test_full_regime_no_drift_no_dd(self):
        _promote_to_capped()
        result = compute_allocation(
            SID, regime_stability=1.0, drift_penalty=0.0, drawdown_frac=0.0
        )
        # base_weight(0.10) * 1.0 * 1.0 * 1.0 = 0.10, capped at 0.05
        assert abs(result - 0.05) < 1e-6  # capped at stage cap

    def test_poor_regime_reduces_allocation(self):
        _promote_to_capped()
        # Use base_weight=0.02 so raw=0.02 < stage_cap=0.05 — stability effect visible
        full = compute_allocation(SID, regime_stability=1.0, base_weight=0.02)
        reduced = compute_allocation(SID, regime_stability=0.5, base_weight=0.02)
        assert reduced < full
        assert abs(full - 0.02) < 1e-6
        assert abs(reduced - 0.01) < 1e-6

    def test_max_drift_zeros_allocation(self):
        _promote_to_capped()
        result = compute_allocation(SID, drift_penalty=1.0)
        assert result == 0.0

    def test_max_drawdown_zeros_allocation(self):
        _promote_to_capped()
        result = compute_allocation(SID, drawdown_frac=1.0)
        assert result == 0.0

    def test_allocation_never_exceeds_stage_cap(self):
        _promote_to_capped()
        # Even with perfect inputs and high base_weight
        result = compute_allocation(
            SID, regime_stability=1.0, drift_penalty=0.0,
            drawdown_frac=0.0, base_weight=1.0
        )
        assert result <= 0.05 + 1e-9  # capped_live cap

    def test_below_min_meaningful_rounds_to_zero(self):
        _promote_to_capped()
        # Very poor stability → tiny allocation → rounds to 0
        result = compute_allocation(
            SID, regime_stability=0.001, drift_penalty=0.0,
            base_weight=0.001
        )
        assert result == 0.0

    def test_drawdown_fraction_clamped_above_one(self):
        _promote_to_capped()
        # drawdown_frac > 1.0 should be treated as 1.0
        result = compute_allocation(SID, drawdown_frac=999.0)
        assert result == 0.0

    def test_negative_drift_clamped_to_zero(self):
        _promote_to_capped()
        # Negative drift penalty should not boost allocation beyond base
        normal = compute_allocation(SID, drift_penalty=0.0)
        clamped = compute_allocation(SID, drift_penalty=-100.0)
        assert abs(normal - clamped) < 1e-9


class TestAllocationSummary:
    def test_summary_has_all_fields(self):
        _promote_to_capped()
        s = allocation_summary(SID)
        for field in ("strategy_id", "stage", "allocation_frac", "stage_cap_frac",
                      "regime_stability", "drift_penalty", "drawdown_frac", "new_risk_allowed"):
            assert field in s, f"missing: {field}"

    def test_summary_new_risk_allowed_false_at_paper(self):
        s = allocation_summary(SID)  # still at paper
        assert s["new_risk_allowed"] is False

    def test_summary_new_risk_allowed_true_at_capped(self):
        _promote_to_capped()
        s = allocation_summary(SID, regime_stability=1.0)
        assert s["new_risk_allowed"] is True
