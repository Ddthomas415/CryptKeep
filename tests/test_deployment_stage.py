"""tests/test_deployment_stage.py

Tests for services/control/deployment_stage.py — the stage machine.

Critical path: any bug here means illegal stage transitions go undetected,
potentially allowing promotion from paper directly to capped_live.
"""
from __future__ import annotations
import pytest
from services.control.deployment_stage import (
    Stage, get_current_stage, promote, demote, force_safe_degraded,
    action_allowed, max_allocation_frac, stage_summary,
)

SID = "test_strategy_ds"


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


class TestDefaultStage:
    def test_fresh_strategy_starts_at_paper(self):
        assert get_current_stage(SID) == Stage.PAPER

    def test_paper_allocation_is_zero(self):
        assert max_allocation_frac(SID) == 0.0

    def test_paper_allows_only_simulate(self):
        ok, _ = action_allowed(SID, "simulate")
        assert ok is True

    def test_paper_blocks_submit(self):
        ok, reason = action_allowed(SID, "submit_full")
        assert ok is False
        assert reason  # has a reason string


class TestPromotion:
    def test_promote_paper_to_shadow(self):
        result = promote(SID, reason="test", actor="test")
        assert result["ok"] is True
        assert result["stage"] == Stage.SHADOW.value
        assert get_current_stage(SID) == Stage.SHADOW

    def test_promote_shadow_to_capped_live(self):
        promote(SID, reason="step1", actor="test")  # paper→shadow
        result = promote(SID, reason="step2", actor="test")
        assert result["ok"] is True
        assert result["stage"] == Stage.CAPPED_LIVE.value

    def test_promote_capped_live_to_scaled_live(self):
        promote(SID, reason="s1", actor="test")
        promote(SID, reason="s2", actor="test")
        result = promote(SID, reason="s3", actor="test")
        assert result["ok"] is True
        assert result["stage"] == Stage.SCALED_LIVE.value

    def test_promote_from_scaled_live_fails(self):
        """Cannot promote beyond scaled_live."""
        for i in range(3):
            promote(SID, reason=f"s{i}", actor="test")
        result = promote(SID, reason="overflow", actor="test")
        assert result["ok"] is False
        assert "already_at_max" in result["reason"]

    def test_promote_from_safe_degraded_fails(self):
        force_safe_degraded(SID, reason="test", actor="test")
        result = promote(SID, reason="attempt", actor="test")
        assert result["ok"] is False
        assert "cannot_promote_from_safe_degraded" in result["reason"]

    def test_cannot_skip_shadow(self):
        """Each promote only moves one step — cannot jump paper→capped_live."""
        result = promote(SID, reason="first_promote", actor="test")
        assert result["stage"] == Stage.SHADOW.value  # only moved to shadow
        assert get_current_stage(SID) == Stage.SHADOW


class TestDemotion:
    def test_demote_shadow_to_safe_degraded_by_default(self):
        """demote() without target goes to safe_degraded."""
        promote(SID, reason="up", actor="test")
        assert get_current_stage(SID) == Stage.SHADOW
        result = demote(SID, reason="going back", actor="test")
        assert result["ok"] is True
        assert get_current_stage(SID) == Stage.SAFE_DEGRADED

    def test_demote_shadow_to_paper_with_explicit_target(self):
        """demote() with target=Stage.PAPER goes to paper."""
        promote(SID, reason="up", actor="test")
        result = demote(SID, reason="going back", actor="test", target=Stage.PAPER)
        assert result["ok"] is True
        assert get_current_stage(SID) == Stage.PAPER

    def test_demote_already_at_target_is_ok(self):
        """Demoting when already at target is a no-op that returns ok=True."""
        result = demote(SID, reason="no-op", actor="test", target=Stage.PAPER)
        assert result["ok"] is True
        assert get_current_stage(SID) == Stage.PAPER


class TestForceSafeDegraded:
    def test_force_from_paper(self):
        result = force_safe_degraded(SID, reason="test", actor="test")
        assert result["ok"] is True
        assert get_current_stage(SID) == Stage.SAFE_DEGRADED

    def test_force_from_any_stage(self):
        for _ in range(2):
            promote(SID, reason="up", actor="test")
        assert get_current_stage(SID) == Stage.CAPPED_LIVE
        force_safe_degraded(SID, reason="emergency", actor="test")
        assert get_current_stage(SID) == Stage.SAFE_DEGRADED

    def test_safe_degraded_blocks_new_risk(self):
        force_safe_degraded(SID, reason="test", actor="test")
        assert max_allocation_frac(SID) == 0.0

    def test_safe_degraded_allows_reduce(self):
        force_safe_degraded(SID, reason="test", actor="test")
        ok, _ = action_allowed(SID, "reduce")
        assert ok is True


class TestStageSummary:
    def test_summary_has_required_fields(self):
        s = stage_summary(SID)
        for field in ("stage", "allowed_actions", "max_alloc_frac", "since_ts"):
            assert field in s, f"missing field: {field}"

    def test_summary_reflects_promotion(self):
        promote(SID, reason="test", actor="test")
        s = stage_summary(SID)
        assert s["stage"] == Stage.SHADOW.value
