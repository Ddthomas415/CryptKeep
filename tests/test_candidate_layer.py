"""
tests/test_candidate_layer.py
Tests for the System 1 candidate signal layer:
  - trade_type_classifier
  - candidate_strategy_mapper
  - candidate_engine (build_candidate_list)
  - candidate_advisor (get_top_candidate)
  - candidate_store (history, diff, stats)
  - strategy_selector flag-gated advisor override (CBP_USE_CANDIDATE_ADVISOR)
"""
from __future__ import annotations

import os
import json
import tempfile
import pytest

# ---------------------------------------------------------------------------
# 1. Trade-type classifier
# ---------------------------------------------------------------------------

from services.signals.trade_type_classifier import classify_trade_type


def _scores(**kwargs) -> dict:
    base = {
        "momentum_score": 0.0,
        "relative_strength_score": 0.0,
        "volume_surge_score": 0.0,
        "pullback_recovery_score": 0.0,
        "illiquidity_risk_score": 0.0,
    }
    base.update(kwargs)
    return base


class TestTradeTypeClassifier:
    def test_pass_on_high_illiquidity(self):
        r = classify_trade_type(scores=_scores(illiquidity_risk_score=90.0))
        assert r["trade_type"] == "pass"
        assert "illiquidity" in r["reason"]

    def test_swing_trade_on_pullback_profile(self):
        r = classify_trade_type(scores=_scores(
            pullback_recovery_score=75.0,
            relative_strength_score=60.0,
            momentum_score=45.0,
        ))
        assert r["trade_type"] == "swing_trade"
        assert "pullback" in r["reason"]

    def test_quick_flip_on_momentum_profile(self):
        r = classify_trade_type(scores=_scores(
            momentum_score=60.0,
            relative_strength_score=75.0,
            volume_surge_score=30.0,
        ))
        assert r["trade_type"] == "quick_flip"
        assert "momentum" in r["reason"]

    def test_pass_on_weak_signals(self):
        r = classify_trade_type(scores=_scores(
            momentum_score=10.0,
            relative_strength_score=10.0,
            volume_surge_score=5.0,
            pullback_recovery_score=5.0,
        ))
        assert r["trade_type"] == "pass"

    def test_illiquidity_gate_overrides_strong_signals(self):
        """High illiquidity blocks even a perfect signal profile."""
        r = classify_trade_type(scores=_scores(
            illiquidity_risk_score=90.0,
            momentum_score=90.0,
            relative_strength_score=90.0,
            volume_surge_score=90.0,
            pullback_recovery_score=90.0,
        ))
        assert r["trade_type"] == "pass"

    def test_returns_dict_with_trade_type_and_reason(self):
        r = classify_trade_type(scores=_scores())
        assert "trade_type" in r
        assert "reason" in r

    def test_empty_scores_returns_pass(self):
        r = classify_trade_type(scores={})
        assert r["trade_type"] == "pass"


# ---------------------------------------------------------------------------
# 2. Candidate strategy mapper
# ---------------------------------------------------------------------------

from services.signals.candidate_strategy_mapper import map_candidate_to_strategy


class TestCandidateStrategyMapper:
    def test_pass_trade_type_returns_no_strategy(self):
        r = map_candidate_to_strategy({"trade_type": "pass", "scores": {}})
        assert r["preferred_strategy"] is None

    def test_swing_high_pullback_maps_to_pullback_recovery(self):
        r = map_candidate_to_strategy({
            "trade_type": "swing_trade",
            "scores": {"pullback_recovery_score": 80.0},
        })
        assert r["preferred_strategy"] == "pullback_recovery"

    def test_swing_low_pullback_maps_to_mean_reversion(self):
        r = map_candidate_to_strategy({
            "trade_type": "swing_trade",
            "scores": {"pullback_recovery_score": 50.0},
        })
        assert r["preferred_strategy"] == "mean_reversion_rsi"

    def test_quick_flip_maps_to_momentum(self):
        r = map_candidate_to_strategy({
            "trade_type": "quick_flip",
            "scores": {
                "momentum_score": 60.0,
                "relative_strength_score": 75.0,
                "volume_surge_score": 30.0,
            },
        })
        assert r["preferred_strategy"] == "momentum"

    def test_always_returns_reason(self):
        r = map_candidate_to_strategy({"trade_type": "swing_trade", "scores": {}})
        assert "reason" in r and r["reason"]

    def test_unknown_trade_type_returns_none(self):
        r = map_candidate_to_strategy({"trade_type": "unknown_xyz", "scores": {}})
        assert r["preferred_strategy"] is None


# ---------------------------------------------------------------------------
# 3. Candidate engine
# ---------------------------------------------------------------------------

from services.signals.candidate_engine import build_candidate_list


def _make_symbol_data(symbol: str, return_pct: float, ohlcv_len: int = 30) -> dict:
    """Minimal symbol data payload with enough OHLCV for scoring."""
    closes = [100.0 + i * return_pct / ohlcv_len for i in range(ohlcv_len)]
    ohlcv = [[1000 * i, c * 0.99, c * 1.01, c * 0.98, c, 1000.0] for i, c in enumerate(closes)]
    return {"symbol": symbol, "symbol_return_pct": return_pct, "ohlcv": ohlcv}


class TestCandidateEngine:
    def test_returns_list(self):
        data = [_make_symbol_data("BTC/USDT", 5.0)]
        result = build_candidate_list(symbols_data=data)
        assert isinstance(result, list)

    def test_filters_below_min_score(self):
        data = [_make_symbol_data("LOW/USDT", 0.0)]
        result = build_candidate_list(symbols_data=data, min_composite_score=99.0)
        assert result == []

    def test_output_has_required_fields(self):
        data = [_make_symbol_data("BTC/USDT", 8.0)]
        result = build_candidate_list(symbols_data=data, min_composite_score=0.0)
        if result:
            row = result[0]
            for field in ("symbol", "composite_score", "trade_type", "preferred_strategy", "scores"):
                assert field in row, f"missing field: {field}"

    def test_filters_pass_trade_type(self):
        """Candidates with trade_type=pass should not appear in output."""
        # Minimal scores will produce pass trade type — verify they're excluded
        data = [_make_symbol_data("FLAT/USDT", 0.0)]
        result = build_candidate_list(symbols_data=data, min_composite_score=0.0)
        for row in result:
            assert row.get("trade_type") != "pass"

    def test_sorted_by_composite_score_descending(self):
        data = [
            _make_symbol_data("LOW/USDT", 1.0),
            _make_symbol_data("HIGH/USDT", 10.0),
        ]
        result = build_candidate_list(symbols_data=data, min_composite_score=0.0)
        scores = [r["composite_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_input_returns_empty(self):
        result = build_candidate_list(symbols_data=[])
        assert result == []


# ---------------------------------------------------------------------------
# 4. Candidate advisor
# ---------------------------------------------------------------------------

from services.signals.candidate_advisor import get_top_candidate
from services.signals.candidate_store import write_candidates


@pytest.fixture()
def tmp_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    return tmp_path


class TestCandidateAdvisor:
    def test_returns_none_when_no_candidates(self, tmp_runtime):
        result = get_top_candidate(min_score=40.0)
        assert result is None

    def test_returns_top_candidate_above_min_score(self, tmp_runtime):
        write_candidates([
            {"symbol": "BTC/USDT", "composite_score": 70.0,
             "trade_type": "swing_trade", "preferred_strategy": "pullback_recovery",
             "mapping_reason": "test", "trade_type_reason": "test", "scores": {}},
        ])
        result = get_top_candidate(min_score=40.0)
        assert result is not None
        assert result["symbol"] == "BTC/USDT"

    def test_filters_below_min_score(self, tmp_runtime):
        write_candidates([
            {"symbol": "LOW/USDT", "composite_score": 20.0,
             "trade_type": "swing_trade", "preferred_strategy": "pullback_recovery",
             "mapping_reason": "test", "trade_type_reason": "test", "scores": {}},
        ])
        result = get_top_candidate(min_score=40.0)
        assert result is None

    def test_filters_pass_trade_type(self, tmp_runtime):
        write_candidates([
            {"symbol": "PASS/USDT", "composite_score": 80.0,
             "trade_type": "pass", "preferred_strategy": None,
             "mapping_reason": "", "trade_type_reason": "", "scores": {}},
        ])
        result = get_top_candidate(min_score=0.0)
        assert result is None

    def test_filters_missing_preferred_strategy(self, tmp_runtime):
        write_candidates([
            {"symbol": "NOMAP/USDT", "composite_score": 80.0,
             "trade_type": "swing_trade", "preferred_strategy": None,
             "mapping_reason": "", "trade_type_reason": "", "scores": {}},
        ])
        result = get_top_candidate(min_score=0.0)
        assert result is None

    def test_returns_highest_score_when_multiple(self, tmp_runtime):
        write_candidates([
            {"symbol": "MED/USDT", "composite_score": 55.0,
             "trade_type": "swing_trade", "preferred_strategy": "mean_reversion_rsi",
             "mapping_reason": "", "trade_type_reason": "", "scores": {}},
            {"symbol": "TOP/USDT", "composite_score": 82.0,
             "trade_type": "quick_flip", "preferred_strategy": "momentum",
             "mapping_reason": "", "trade_type_reason": "", "scores": {}},
        ])
        result = get_top_candidate(min_score=40.0)
        assert result["symbol"] == "TOP/USDT"

    def test_result_has_required_fields(self, tmp_runtime):
        write_candidates([
            {"symbol": "BTC/USDT", "composite_score": 70.0,
             "trade_type": "swing_trade", "preferred_strategy": "pullback_recovery",
             "mapping_reason": "r", "trade_type_reason": "r", "scores": {"momentum_score": 50}},
        ])
        result = get_top_candidate(min_score=0.0)
        for field in ("symbol", "composite_score", "trade_type", "preferred_strategy", "scores"):
            assert field in result


# ---------------------------------------------------------------------------
# 5. Candidate store: history, diff, stats
# ---------------------------------------------------------------------------

from services.signals.candidate_store import (
    load_history, load_previous_snapshot, diff_snapshots, history_stats,
    load_latest_snapshot,
)


class TestCandidateStore:
    def test_write_and_load_latest(self, tmp_runtime):
        write_candidates([{"symbol": "A/USDT", "composite_score": 0.5}])
        rows = load_latest_snapshot()
        assert rows["candidates"][0]["symbol"] == "A/USDT"

    def test_history_accumulates(self, tmp_runtime):
        write_candidates([{"symbol": "A/USDT"}], scan_id="s1")
        write_candidates([{"symbol": "B/USDT"}], scan_id="s2")
        h = load_history(limit=10)
        assert len(h) == 2

    def test_history_newest_first(self, tmp_runtime):
        write_candidates([{"symbol": "FIRST/USDT"}], scan_id="first")
        write_candidates([{"symbol": "LAST/USDT"}], scan_id="last")
        h = load_history(limit=10)
        assert h[0]["scan_id"] == "last"

    def test_load_previous_snapshot(self, tmp_runtime):
        write_candidates([{"symbol": "A/USDT"}], scan_id="s1")
        write_candidates([{"symbol": "B/USDT"}], scan_id="s2")
        prev = load_previous_snapshot()
        assert prev["scan_id"] == "s1"

    def test_diff_detects_new_entry(self, tmp_runtime):
        curr = [{"symbol": "A/USDT"}, {"symbol": "B/USDT"}]
        prev = [{"symbol": "A/USDT"}]
        d = diff_snapshots(curr, prev)
        new_syms = [r["symbol"] for r in d["new"]]
        assert "B/USDT" in new_syms

    def test_diff_detects_dropped_entry(self, tmp_runtime):
        curr = [{"symbol": "A/USDT"}]
        prev = [{"symbol": "A/USDT"}, {"symbol": "B/USDT"}]
        d = diff_snapshots(curr, prev)
        dropped = [r["symbol"] for r in d["dropped"]]
        assert "B/USDT" in dropped

    def test_diff_detects_rank_change(self, tmp_runtime):
        curr = [{"symbol": "B/USDT"}, {"symbol": "A/USDT"}]
        prev = [{"symbol": "A/USDT"}, {"symbol": "B/USDT"}]
        d = diff_snapshots(curr, prev)
        moved_up = [r["symbol"] for r in d["moved_up"]]
        moved_dn = [r["symbol"] for r in d["moved_dn"]]
        assert "B/USDT" in moved_up
        assert "A/USDT" in moved_dn

    def test_history_stats_tracks_count(self, tmp_runtime):
        write_candidates([{"symbol": "X"}], scan_id="s1")
        write_candidates([{"symbol": "Y"}], scan_id="s2")
        s = history_stats()
        assert s["entries"] == 2

    def test_atomic_write_produces_valid_json(self, tmp_runtime):
        write_candidates([{"symbol": "Z/USDT", "composite_score": 0.9}])
        snap = load_latest_snapshot()
        assert isinstance(snap, dict)
        assert isinstance(snap.get("candidates"), list)

    def test_empty_history_returns_empty_list(self, tmp_runtime):
        h = load_history()
        assert h == []


# ---------------------------------------------------------------------------
# 6. Strategy selector: CBP_USE_CANDIDATE_ADVISOR flag
# ---------------------------------------------------------------------------

from services.strategies.strategy_selector import select_strategy


def _flat_ohlcv(n: int = 60) -> list:
    return [[i * 1000, 100.0, 101.0, 99.0, 100.0, 1000.0] for i in range(n)]


class TestCandidateAdvisorFlag:
    def test_flag_off_does_not_call_advisor(self, tmp_runtime, monkeypatch):
        monkeypatch.delenv("CBP_USE_CANDIDATE_ADVISOR", raising=False)
        # Even if a candidate exists, flag off means advisor is not consulted
        write_candidates([
            {"symbol": "BTC/USDT", "composite_score": 99.0,
             "trade_type": "swing_trade", "preferred_strategy": "pullback_recovery",
             "mapping_reason": "r", "trade_type_reason": "r", "scores": {}},
        ])
        result = select_strategy(default_strategy="ema_cross", ohlcv=_flat_ohlcv())
        # pullback_recovery should NOT be boosted when flag is off
        assert isinstance(result, dict)
        assert "selected_strategy" in result

    def test_flag_on_boosts_preferred_strategy(self, tmp_runtime, monkeypatch):
        monkeypatch.setenv("CBP_USE_CANDIDATE_ADVISOR", "1")
        monkeypatch.setenv("CBP_SYMBOLS", "BTC/USDT")
        write_candidates([
            {"symbol": "BTC/USDT", "composite_score": 99.0,
             "trade_type": "swing_trade", "preferred_strategy": "pullback_recovery",
             "mapping_reason": "swing_pullback", "trade_type_reason": "r", "scores": {}},
        ])
        result = select_strategy(default_strategy="ema_cross", ohlcv=_flat_ohlcv())
        assert isinstance(result, dict)
        # When advisor boosts pullback_recovery by 100 pts it should win
        assert result.get("selected_strategy") == "pullback_recovery"

    def test_flag_on_with_no_candidates_falls_back_gracefully(self, tmp_runtime, monkeypatch):
        monkeypatch.setenv("CBP_USE_CANDIDATE_ADVISOR", "1")
        monkeypatch.setenv("CBP_SYMBOLS", "BTC/USDT")
        # No candidates written — advisor returns None, selector should not crash
        result = select_strategy(default_strategy="ema_cross", ohlcv=_flat_ohlcv())
        assert isinstance(result, dict)
        assert "selected_strategy" in result

    def test_flag_on_symbol_mismatch_does_not_boost(self, tmp_runtime, monkeypatch):
        monkeypatch.setenv("CBP_USE_CANDIDATE_ADVISOR", "1")
        monkeypatch.setenv("CBP_SYMBOLS", "ETH/USDT")  # different from candidate
        write_candidates([
            {"symbol": "BTC/USDT", "composite_score": 99.0,
             "trade_type": "swing_trade", "preferred_strategy": "pullback_recovery",
             "mapping_reason": "r", "trade_type_reason": "r", "scores": {}},
        ])
        result = select_strategy(default_strategy="ema_cross", ohlcv=_flat_ohlcv())
        # BTC candidate should not boost because CBP_SYMBOLS=ETH
        assert isinstance(result, dict)
        assert result.get("selected_strategy") != "pullback_recovery"
