"""tests/test_retirement_checker.py

Tests for services/control/retirement_checker.py — the service-layer
retirement threshold evaluator used by the control kernel.
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fill(pnl: float | None = None, side: str = "sell") -> dict:
    return {
        "record_type": "fill", "timestamp": _now(),
        "side": side, "fill_price": 85000.0,
        "slippage_points": 5.0, "slippage_pct": 0.006, "fees_paid": 1.70,
        "pnl_usd": pnl,
    }


def _session(drawdown: float = 0.0) -> dict:
    return {
        "record_type": "session", "timestamp": _now(),
        "regime_at_open": "trending", "halts_triggered": [],
        "manual_overrides": [], "reconciliation_result": "pass",
        "drawdown_from_peak": drawdown, "kill_switch_tested": False,
        "ops_checks_passed": True, "critical_error": False,
    }


class TestCheckRetirementTriggers:
    def test_no_data_no_triggers(self):
        from services.control.retirement_checker import check_retirement_triggers
        result = check_retirement_triggers([], [])
        assert result["retirement_required"] is False
        assert result["triggers_fired"] == []

    def test_positive_expectancy_no_trigger(self):
        from services.control.retirement_checker import check_retirement_triggers
        fills = [_fill(pnl=100.0) for _ in range(12)]
        result = check_retirement_triggers(fills, [])
        assert result["retirement_required"] is False
        assert not any("expectancy" in t for t in result["triggers_fired"])

    def test_negative_expectancy_fires_trigger(self):
        from services.control.retirement_checker import check_retirement_triggers
        fills = [_fill(pnl=-50.0) for _ in range(12)]
        result = check_retirement_triggers(fills, [])
        assert any("expectancy_negative" in t for t in result["triggers_fired"])
        assert result["single_trigger_review"] is True
        assert result["retirement_required"] is False  # only one trigger

    def test_fewer_than_10_fills_no_expectancy_trigger(self):
        from services.control.retirement_checker import check_retirement_triggers
        fills = [_fill(pnl=-500.0) for _ in range(9)]
        result = check_retirement_triggers(fills, [])
        assert not any("expectancy" in t for t in result["triggers_fired"])

    def test_drawdown_exceeded_fires_trigger(self):
        from services.control.retirement_checker import check_retirement_triggers
        sessions = [_session(drawdown=15.0)]
        result = check_retirement_triggers([], sessions, max_drawdown_pct=12.0)
        assert any("drawdown_exceeded" in t for t in result["triggers_fired"])
        assert result["single_trigger_review"] is True

    def test_drawdown_within_limit_no_trigger(self):
        from services.control.retirement_checker import check_retirement_triggers
        sessions = [_session(drawdown=5.0)]
        result = check_retirement_triggers([], sessions, max_drawdown_pct=12.0)
        assert not any("drawdown" in t for t in result["triggers_fired"])

    def test_two_triggers_requires_retirement(self):
        from services.control.retirement_checker import check_retirement_triggers
        fills = [_fill(pnl=-50.0) for _ in range(12)]
        sessions = [_session(drawdown=15.0)]
        result = check_retirement_triggers(fills, sessions, max_drawdown_pct=12.0)
        assert result["retirement_required"] is True
        assert len(result["triggers_fired"]) == 2

    def test_result_always_has_required_keys(self):
        from services.control.retirement_checker import check_retirement_triggers
        result = check_retirement_triggers([], [])
        assert "triggers_fired" in result
        assert "retirement_required" in result
        assert "single_trigger_review" in result
        assert "note" in result

    def test_fills_without_pnl_field_ignored(self):
        from services.control.retirement_checker import check_retirement_triggers
        # Fills with no pnl_usd (orders) should not count toward expectancy
        fills = [{"record_type": "fill", "fill_price": 85000.0} for _ in range(15)]
        result = check_retirement_triggers(fills, [])
        assert not any("expectancy" in t for t in result["triggers_fired"])


class TestLoadAllEvidence:
    def test_empty_dir_returns_empty_lists(self, tmp_path):
        from services.control.retirement_checker import load_all_evidence
        result = load_all_evidence(tmp_path / "nonexistent")
        assert result == {"signal": [], "order": [], "fill": [], "session": [], "drawdown": []}

    def test_loads_signal_jsonl(self, tmp_path):
        from services.control.retirement_checker import load_all_evidence
        rec = {"record_type": "signal", "price": 85000.0, "signal_direction": "long"}
        (tmp_path / "signal_2026-04-16.jsonl").write_text(json.dumps(rec) + "\n")
        result = load_all_evidence(tmp_path)
        assert len(result["signal"]) == 1
        assert result["signal"][0]["price"] == 85000.0

    def test_loads_multiple_record_types(self, tmp_path):
        from services.control.retirement_checker import load_all_evidence
        (tmp_path / "signal_2026-04-16.jsonl").write_text(
            json.dumps({"record_type": "signal", "price": 1.0}) + "\n"
        )
        (tmp_path / "fill_2026-04-16.jsonl").write_text(
            json.dumps({"record_type": "fill", "pnl_usd": 100.0}) + "\n"
        )
        result = load_all_evidence(tmp_path)
        assert len(result["signal"]) == 1
        assert len(result["fill"]) == 1

    def test_skips_malformed_jsonl_lines(self, tmp_path):
        from services.control.retirement_checker import load_all_evidence
        (tmp_path / "signal_2026-04-16.jsonl").write_text(
            json.dumps({"record_type": "signal"}) + "\n" +
            "NOT VALID JSON\n" +
            json.dumps({"record_type": "signal"}) + "\n"
        )
        result = load_all_evidence(tmp_path)
        assert len(result["signal"]) == 2  # bad line skipped, 2 good records

    def test_loads_golden_sample_artifacts(self):
        """Validates against committed golden test artifacts."""
        from services.control.retirement_checker import load_all_evidence
        golden_dir = Path("sample_data/evidence/es_daily_trend_v1")
        if not golden_dir.exists():
            pytest.skip("golden artifacts not present")
        result = load_all_evidence(golden_dir)
        # Signal records must have required fields
        for rec in result["signal"]:
            assert "signal_direction" in rec
            assert "regime_flag" in rec
        # Fill records must have slippage
        for rec in result["fill"]:
            assert "slippage_pct" in rec
        # At least one chop record in golden data
        chop_signals = [s for s in result["signal"] if s.get("regime_flag") == "chop"]
        assert len(chop_signals) >= 1, "golden data should include a chop regime signal"

    def test_golden_fills_have_pnl_on_sells(self):
        """Sell fills in golden data should have pnl_usd populated."""
        from services.control.retirement_checker import load_all_evidence
        golden_dir = Path("sample_data/evidence/es_daily_trend_v1")
        if not golden_dir.exists():
            pytest.skip("golden artifacts not present")
        result = load_all_evidence(golden_dir)
        sell_fills = [f for f in result["fill"] if f.get("side") == "sell"]
        assert all(f.get("pnl_usd") is not None for f in sell_fills), \
            "all sell fills in golden data must have pnl_usd"
